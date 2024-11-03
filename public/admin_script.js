document.addEventListener('DOMContentLoaded', () => {
    loadUsers();
    loadStatistics();
});

// Function to load users
async function loadUsers() {
    try {
        const response = await fetch('/load');
        const users = await response.json();
        displayUsers(users);
    } catch (error) {
        console.error("Error loading users:", error);
    }
}

// Function to display users
function displayUsers(users) {
    const userList = document.getElementById('userList');
    userList.innerHTML = '';  // Clear previous content

    users.forEach(user => {
        const userDiv = document.createElement('div');
        userDiv.className = 'user';

        userDiv.innerHTML = `
            <p><strong>ID:</strong> ${user.id}</p>
            <p><strong>Email:</strong> ${user.email}</p>
            <p><strong>Time of Visit:</strong> ${user.timeOfVisit}</p>
            <button onclick="deleteUser('${user.id}')">Delete</button>
            <button onclick="editUser('${user.id}')">Edit</button>
        `;
        
        userList.appendChild(userDiv);
    });
}

// Delete a user
async function deleteUser(userId) {
    try {
        await fetch(`/delete/${userId}`, { method: 'DELETE' });
        alert('User deleted');
        loadUsers();
    } catch (error) {
        console.error("Error deleting user:", error);
    }
}

// Sort users
async function sortUsers() {
    const field = document.getElementById('sortField').value;
    const order = document.getElementById('sortOrder').value;

    try {
        const response = await fetch(`/sort?field=${field}&order=${order}`);
        const sortedUsers = await response.json();
        displayUsers(sortedUsers);
    } catch (error) {
        console.error("Error sorting users:", error);
    }
}

// Filter users
async function filterUsers() {
    const maxTime = document.getElementById('maxTimeVisit').value;
    const excludeWhois = document.getElementById('excludeWhoisNone').checked;

    // Prepare query parameters
    let url = `/filter-users?max_time_of_visit=${maxTime}`;
    
    if (excludeWhois) {
        url += `&exclude_whois_none=${excludeWhois}`;
    } else {
        url += `&exclude_whois_none=false`;
    }

    try {
        const response = await fetch(url);
        const filteredUsers = await response.json();
        displayUsers(filteredUsers);
    } catch (error) {
        console.error("Error filtering users:", error);
    }
}


// Load statistics
async function loadStatistics() {
    try {
        const response = await fetch('/stats');
        const stats = await response.json();
        displayStatistics(stats);
    } catch (error) {
        console.error("Error loading statistics:", error);
    }
}

// Display statistics
function displayStatistics(stats) {
    const statsDiv = document.getElementById('statistics');
    statsDiv.innerHTML = `
        <p><strong>Total Users:</strong> ${stats.total_users}</p>
        <p><strong>Average Time of Visit:</strong> ${stats.average_time_of_visit}</p>
        <p><strong>Users by Location:</strong> ${JSON.stringify(stats.users_by_location)}</p>
    `;
}
