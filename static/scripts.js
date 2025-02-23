const socket = io();

// Q&A Functionality
function sendMessage() {
    const message = document.getElementById('messageInput').value;
    if (message.trim() !== "") {
        socket.send(message);
        document.getElementById('messageInput').value = '';
    }
}

socket.on('message', function(msg) {
    const li = document.createElement('li');
    li.textContent = msg;
    document.getElementById('messages').appendChild(li);
});

// Poll Functionality
function submitPoll() {
    const selected = document.querySelector('input[name="poll"]:checked');
    if (selected) {
        const vote = selected.value;
        socket.emit('poll_vote', vote);
        document.getElementById('pollForm').style.display = 'none'; // Hide the poll form after voting
    } else {
        alert("Please select an option before submitting.");
    }
}

socket.on('poll_vote', function(vote) {
    const pollResults = document.getElementById('pollResults');
    pollResults.innerHTML += `<p>Vote received: ${vote}</p>`;
});