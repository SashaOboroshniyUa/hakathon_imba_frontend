from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, id, username, gmail, password, email_verified):
        self.id = id
        self.username = username
        self.gmail = gmail
        self.password = password
        self.email_verified = email_verified
