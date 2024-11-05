# This script is used separately to create a new user in the database for the login page. It is not part of the main application.

from ressources.user import User

username = input("Enter username: ")
password = input("Enter password: ")

user = User.create_user(username, password)
print(f"User {username} created successfully")