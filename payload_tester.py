import requests
import random
import concurrent.futures
from faker import Faker

# Initialize Faker for generating random user data
fake = Faker()

# Base URL of the Flask app (change if needed)
BASE_URL = "http://pat.infolab.ecam.be:61818"

def create_user():
    """Function to create a user via the /update-db route."""
    user_data = {
        "name": fake.name(),
        "email": fake.email(),
        "age": random.randint(18, 99)
    }
    
    response = requests.post(f"{BASE_URL}/update-db", json=user_data)
    return response.json()

def load_users():
    """Function to load users via the /load route."""
    response = requests.get(f"{BASE_URL}/load")
    return response.json()

def delete_all_users():
    """Function to delete all users via the /delete-all route."""
    response = requests.delete(f"{BASE_URL}/delete-all")
    return response.json()

def main():
    # Step 1: Create users concurrently
    created_users = []
    user_count = 100000  # Number of users to create
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(create_user): i for i in range(user_count)}
        for future in concurrent.futures.as_completed(futures):
            try:
                created_users.append(future.result())
            except Exception as e:
                print(f"Error creating user: {e}")

    print(f"Created users: {len(created_users)}")

    # Step 2: Load users five times
    for _ in range(5):
        users = load_users()
        print(f"Loaded users: {len(users)}")

    # Step 3: Delete all users
    delete_result = delete_all_users()
    print(f"Delete all users response: {delete_result}")

if __name__ == "__main__":
    main()
