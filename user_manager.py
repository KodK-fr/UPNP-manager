import json
import os

class UserManager:
    def __init__(self, users_file='users.json'):
        self.users_file = users_file
        self.users = self.load_users()

    def load_users(self):
        if os.path.exists(self.users_file):
            with open(self.users_file, 'r') as f:
                return json.load(f)
        return {}

    def authenticate(self, username, password):
        user = self.users.get(username)
        return user and user['password'] == password

    def add_user(self, username, password, role='user'):
        self.users[username] = {'password': password, 'role': role}
        self.save_users()

    def save_users(self):
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f)