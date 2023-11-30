import { connect } from 'q2-tecton-sdk';

const button = document.querySelector('q2-btn');
const input = document.querySelector('q2-input');
const messages = document.getElementById('messages');

connect().then(capabilities => {
  window.tecton = capabilities; // just for easy debugging, can be removed
  capabilities.sources
    .requestExtensionData({ route: 'default' })
    .then(response => {
      capabilities.actions.setTitle(response.data.message);
    })
    .catch(error => showError(error))
    .finally(() => capabilities.actions.setFetching(false));

  button.addEventListener('click', submit);

  function submit() {
    let name = input.value;

    capabilities.sources
      .requestExtensionData({
        route: 'submit',
        body: { name: name }
      })
      .then(response => {
        const listItem = document.createElement("li");
        listItem.innerText = `Hi ${response.data.name} the server date is ${response.data.date}.`;
        messages.append(listItem);
      })
      .catch(error => showError(error));
  }

  function showError(error) {
    capabilities.actions.showModal({
      title: 'Error',
      message: error.data.message,
      modalType: 'error'
    });
  }
});
