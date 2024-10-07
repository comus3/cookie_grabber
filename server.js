const express = require('express');
const app = express();
const path = require('path');
const fs = require('fs');
const fetch = require('node-fetch');

// Parse JSON bodies (as sent by API clients)
app.use(express.json());

// Serve static files from the "public" directory
app.use(express.static(path.join(__dirname, 'public')));

const apiKeyPath = path.join(__dirname, 'ressources', 'api.json');
let apiKey = '';
let whoIsapiKey = '';

try {
    const data = fs.readFileSync(apiKeyPath, 'utf8');
    const apiData = JSON.parse(data);
    apiKey = apiData.apiKey;
    whoIsapiKey = apiData.whoIs;  // WHOIS API key
    console.log("API Key loaded:", apiKey);
    console.log("WhoIs API Key loaded:", whoIsapiKey);
} catch (err) {
    console.error('Error reading API key file:', err);
}

// Path to your `db.json` file
const dbFilePath = path.join(__dirname, 'db.json');

// Helper function to read the current data from `db.json`
function readDatabase() {
    try {
        const data = fs.readFileSync(dbFilePath, 'utf8');
        return JSON.parse(data);
    } catch (err) {
        console.error('Error reading db.json:', err);
        return { users: [] };  // Return an empty structure if the file doesn't exist or is corrupted
    }
}

// Helper function to write updated data to `db.json`
function writeDatabase(data) {
    try {
        fs.writeFileSync(dbFilePath, JSON.stringify(data, null, 4), 'utf8');
        console.log('Database updated successfully.');
    } catch (err) {
        console.error('Error writing to db.json:', err);
    }
}
// Import the xml2js library to parse XML
const xml2js = require('xml2js');

// Route to handle user data and perform API requests server-side
app.post('/update-db', async (req, res) => {
    try {
        const user = req.body;

        console.log("User info received:", user);

        // Get user's IP address from the request
        const ipAddress = req.headers['x-forwarded-for'] || req.socket.remoteAddress;

        // Fetch IP info using ipinfo.io
        const ipInfoResponse = await fetch(`https://ipinfo.io/${ipAddress}/json?token=${apiKey}`);
        console.log("Request sent to IP info API:", `https://ipinfo.io/${ipAddress}/json?token=${apiKey}`);
        console.log("IP Info request status:", ipInfoResponse.status);
        if (!ipInfoResponse.ok) {
            throw new Error('Failed to fetch IP info');
        }
        const ipInfo = await ipInfoResponse.json();

        console.log("IP Info received from external API:", ipInfo);

        // Add IP info and location to the user object
        user.ipAddress = ipAddress;
        user.location = {
            city: ipInfo.city || null,
            region: ipInfo.region || null,
            country: ipInfo.country || null,
            postal: ipInfo.postal || null,
            org: ipInfo.org || null,
            location: ipInfo.loc || null
        };

        // Fetch WHOIS data for the IP address
        const whoisResponse = await fetch(`https://www.whoisxmlapi.com/whoisserver/WhoisService?apiKey=${whoIsapiKey}&domainName=${ipAddress}&outputFormat=JSON`);
        console.log("Request sent to WHOIS API:", `https://www.whoisxmlapi.com/whoisserver/WhoisService?apiKey=${whoIsapiKey}&domainName=${ipAddress}&outputFormat=JSON`);
        console.log("WHOIS API request status:", whoisResponse.status);
        if (!whoisResponse.ok) {
            throw new Error('Failed to fetch WHOIS data');
        }
        const whoisData = await whoisResponse.json();

        console.log("WHOIS data received from API:", whoisData);

        // Add WHOIS data to the user object
        user.whoisData = whoisData;

        console.log('Final user data to save:', user);

        // Read the existing data from the database
        const dbData = readDatabase();

        // Add the new user to the users array
        dbData.users.push(user);

        // Write the updated data back to db.json
        writeDatabase(dbData);

        // Send a success response to the client
        res.status(200).json({ message: 'User data processed and saved successfully' });
    } catch (error) {
        console.error("Error processing user data:", error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Fallback route for serving index.html
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Start the server
app.listen(3000, () => {
    console.log('Server is running on http://localhost:3000');
});
