window.addEventListener('load', async () => {
    console.log("User detected, gathering information...");

    // Initialize FingerprintJS
    const fp = await FingerprintJS.load();
    const result = await fp.get();

    // Get the fingerprint
    const fingerprint = result.visitorId;
    const fingerprintData = result.components;

    // Get cookies from the document
    const cookies = document.cookie.split('; ').map(cookie => cookie.split('='));
    const cookieObj = Object.fromEntries(cookies);

    const networkInfo = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
    const connectionType = networkInfo ? networkInfo.effectiveType : 'unknown';

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

    // Create the user object with all gathered information
    const user = {
        id: Date.now(), // Unique ID based on the current timestamp
        'time of visit': timeOfVisit,
        cookies: cookieObj,
        fingerprint: fingerprint, // Include fingerprint
        fingerprintData: fingerprintData,
        userAgent: userAgent,
        screenResolution: {
            width: screenWidth,
            height: screenHeight
        },
        language: language,
        timezone: timezone,
        platform: navigator.platform,
        networkInfo: networkInfo,
        connectionType: connectionType
    };

    try {
        // Send the user data to the server for further processing
        const dbResponse = await fetch('/update-db', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(user)
        });
        if (!dbResponse.ok) {
            throw new Error('Failed to update the database');
        }
        console.log("User data sent to server successfully.");

        // Generate the download file
        const fileResponse = await fetch('/generate-file', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ userId: user.id, userData: user })
        });
        
        if (!fileResponse.ok) {
            throw new Error('Failed to generate file');
        }

        // Retrieve the file name from the response
        const fileData = await fileResponse.json();
        const fileName = fileData.fileName;

        // Redirect to the data summary page with the user ID and file name
        window.location.href = `/data_summary.html?userId=${user.id}&file=${encodeURIComponent(fileName)}`;

    } catch (error) {
        console.error("Error:", error);
    } finally {
        // Redirect to the awareness info page using the URL passed from Jinja
        console.log("Redirecting to awareness_info...");
        window.location.href = redirectToAwarenessInfo; // Use the variable for redirection
    }
});
