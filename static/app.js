document.getElementById('send-btn').addEventListener('click', () => {
    const userInput = document.getElementById('user-input').value;
    if (userInput.trim() === '') return;

    // Add user message to chat box
    addMessage('user', userInput);

    // Send the message to the Flask backend
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userInput }),
    })
    .then(response => response.json())
    .then(data => {
        addMessage('bot', data.response);
    });

    // Clear the input field
    document.getElementById('user-input').value = '';
});

function addMessage(sender, text) {
    const chatBox = document.getElementById('chat-box');
    const message = document.createElement('div');
    message.classList.add('message', sender);
    message.textContent = text;
    chatBox.appendChild(message);
    chatBox.scrollTop = chatBox.scrollHeight;
}
