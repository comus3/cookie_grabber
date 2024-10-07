const express = require('express');
const fs = require('fs');
const bodyParser = require('body-parser');
const app = express();
const PORT = 3000;

// Middleware to parse JSON
app.use(bodyParser.json());

// Serve the HTML file
app.use(express.static(__dirname));

// Endpoint to update the db.json file
app.post('/update-db', (req, res) => {
    const user = req.body;

    // Read the existing db.json
    fs.readFile('db.json', (err, data) => {
        if (err) {
            return res.status(500).send('Error reading database');
        }
        
        const db = JSON.parse(data);
        db.users.push(user); // Add the new user
        
        // Write the updated db.json
        fs.writeFile('db.json', JSON.stringify(db, null, 2), (err) => {
            if (err) {
                return res.status(500).send('Error updating database');
            }
            res.status(200).send('User data saved successfully');
        });
    });
});

// Start the server
app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});
