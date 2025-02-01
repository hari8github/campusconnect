document.addEventListener('DOMContentLoaded', function () {
  const signupForm = document.getElementById('signup-form');
  const successMessage = document.getElementById('success-message');
  const loginBtn = document.getElementById('login-btn');

  // Handle form submission
  signupForm.addEventListener('submit', async function (event) {
    event.preventDefault();

    // Validate form inputs
    const firstName = document.getElementById('first-name').value.trim();
    const lastName = document.getElementById('last-name').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value.trim();
    const confirmPassword = document.getElementById('confirm-password').value.trim();
    const institution = document.getElementById('institution').value.trim();
    const course = document.getElementById('course').value.trim();
    const terms = document.getElementById('terms').checked;

    // Basic validation
    if (!firstName || !lastName || !email || !password || !confirmPassword || !institution || !course || !terms) {
      alert('Please fill out all fields and agree to the terms and conditions.');
      return;
    }

    // Check if passwords match
    if (password !== confirmPassword) {
      alert('Passwords do not match. Please try again.');
      return;
    }

    // Prepare the data for submission
    const formData = {
      first_name: firstName,
      last_name: lastName,
      email: email,
      password: password,
      confirmPassword: confirmPassword,
      institution: institution,
      course: course
    };

    try {
      // Send the data to the server - Updated route to match Flask blueprint
      const response = await fetch('/signup/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      const result = await response.json();

      if (response.ok) {
        // Clear the form
        signupForm.reset();
        
        // Display success message
        successMessage.textContent = result.message;
        successMessage.classList.remove('hidden');
        
        // Redirect to login page after successful signup
        setTimeout(() => {
          window.location.href = '/';
        }, 1000);
      } else {
        // Show specific error message from server
        alert(result.message || 'Failed to sign up. Please try again.');
      }
    } catch (error) {
      console.error('Error:', error);
      alert('An error occurred while signing up. Please try again later.');
    }
  });
});