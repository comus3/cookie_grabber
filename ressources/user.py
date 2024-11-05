from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

client = MongoClient('mongodb://localhost:27017/')
db = client.cookie_awareness

class User:
    def __init__(self, username):
        self.username = username
        self.user_data = db.admins.find_one({"username": username})

    def is_authenticated(self):
        return True
    
    def get_username(self):
        return self.username

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.user_data['_id'])

    @staticmethod
    def validate_login(username, password):
        user = db.admins.find_one({"username": username})
        if user and check_password_hash(user['password'], password):
            return User(username)
        return None

    @staticmethod
    def create_user(username, password):
        hashed_password = generate_password_hash(password)
        db.admins.insert_one({"username": username, "password": hashed_password})
