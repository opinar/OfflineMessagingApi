from app import login_manager
from flask_login import UserMixin
from app import db


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# User Class/Model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(200), unique=True)
    password = db.Column(db.String(60), nullable=False)
    blocked_users = db.Column(db.PickleType, nullable=True)

    def __init__(self, username, email, password, blocked_users):
        self.username = username
        self.email = email
        self.password = password
        self.blocked_users = blocked_users
