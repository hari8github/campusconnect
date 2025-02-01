document.addEventListener('DOMContentLoaded', function () {
    const loginForm = document.getElementById('login-form');
    const sessionMessage = document.getElementById('session-message');

    console.log('DOM fully loaded and parsed'); // Debugging

    // Login Form Handling
    loginForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // Prevent default form submission
        console.log('Login form submitted'); // Debugging

        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        console.log('Username:', username); // Debugging
        console.log('Password:', password); // Debugging

        try {
            const response = await fetch('/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password }),
            });

            console.log('Response status:', response.status); // Debugging

            if (response.ok) {
                // Show success message
                sessionMessage.style.display = 'block';
                sessionMessage.textContent = 'Login successful! Redirecting...';
                sessionMessage.style.color = 'green';
                sessionMessage.classList.remove('error');
                sessionMessage.classList.add('success');

                // Redirect to chatbot page after 2 seconds
                setTimeout(() => {
                    window.location.href = '/chatbot';
                }, 500);
            } else {
                // Show error message
                sessionMessage.style.display = 'block';
                sessionMessage.textContent = 'Invalid username or password';
                sessionMessage.style.color = 'red';
                sessionMessage.classList.remove('success');
                sessionMessage.classList.add('error');
            }
        } catch (error) {
            console.error('Error during login:', error); // Debugging
            // Show error message for network or server issues
            sessionMessage.style.display = 'block';
            sessionMessage.textContent = 'There was an error during login. Please try again.';
            sessionMessage.style.color = 'red';
            sessionMessage.classList.remove('success');
            sessionMessage.classList.add('error');
        }
    });
});