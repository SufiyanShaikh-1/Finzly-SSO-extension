"""
ExampleSSO Extension
"""

import base64
import uuid

from q2_sdk.core.http_handlers.sso_handler import Q2SSORequestHandler, Q2SSOResponse, ResponseType
from .install.db_plan import DbPlan
from q2_sdk.models import saml_response
from q2_sdk.hq.models.sso_response import UserLevelConfig, UserLevelConfigList


class FinzlySSOHandler(Q2SSORequestHandler):

    VENDOR_CONFIGS = {
        # Assertion consumer service (ACS) URL. This URL will have the following format: <marketplace_base_url>/saml/login
        'ACS_URL': 'https://security-uat2.finzly.io/auth/realms/BANKOS-UAT2-SANDBOX-CUSTOMER/broker/saml/endpoint/clients/clientportal',

        # Identity Provider id of who sent the message
        'IDP_ENTITY_ID': 'q2.finzly.cashos.sso',

        # Service Provider id of who received the message
        'SP_ENTITY_ID': 'https://security-uat2.finzly.io/auth/realms/BANKOS-UAT2-SANDBOX-CUSTOMER',

        # Target URL or destination of the response
        'TARGET_DESTINATION': 'https://security-uat2.finzly.io/auth/realms/BANKOS-UAT2-SANDBOX-CUSTOMER/broker/saml/endpoint/clients/clientportal'
    }

    #Whether the result is displayed in an overpanel or a new tab
    RENDER_IN_NEW_WINDOW = True

    DB_PLAN = DbPlan()

    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        self.unique_user_identifier = None
        self.third_party_element_name = self.DB_PLAN.third_party_element_name

    async def default(self):
        self.unique_user_identifier = self.vendor_configs.get(self.third_party_element_name)
        user_config_list = None
        if not self.unique_user_identifier:
            self.unique_user_identifier = str(uuid.uuid4())
            user_config_value = UserLevelConfig(self.third_party_element_name, self.unique_user_identifier)
            user_config_list = UserLevelConfigList(self.vendor_id, [user_config_value])

        response = await self.get_saml_response()

        bindings = {
            'url': self.vendor_configs.get('ACS_URL'),
            'saml_response': base64.b64encode(response).decode(),
            'relay_state': 'black'
        }

        html = self.get_template('sso.html.jinja2', bindings)

        response = Q2SSOResponse(ResponseType.HTML, response=html, user_level_config_list=user_config_list)
        return response

    async def get_saml_response(self):
        document = saml_response.Q2SamlResponse(
            issuer=self.vendor_configs.get('IDP_ENTITY_ID'),
            audience=self.vendor_configs.get('SP_ENTITY_ID'),
            #destination=self.vendor_configs.get('TARGET_DESTINATION'),
            destination= 'https://security-uat2.finzly.io/auth/realms/BANKOS-UAT2-SANDBOX-CUSTOMER/broker/saml/endpoint/clients/clientportal',
            subject_principal=f'{self.online_user.email_address}',
            attributes={
                'UUID': self.unique_user_identifier,
                'Email': self.online_user.email_address,
                'FirstName': self.online_user.first_name,
                'LastName': self.online_user.last_name,
                'Role': 'Online Customer',
                'CompanyID': ''
            }
        )

        #This returns a file path with both the certificate and the private key in one file
        cert = self.vault.get_certificate('example', self.hq_credentials)

        signed_document = document.sign(cert)

        self.logger.debug('SAML Response: %s', signed_document)

        return signed_document
