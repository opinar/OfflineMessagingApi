from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_marshmallow import Marshmallow
from flask_login import LoginManager, UserMixin
from datetime import datetime
import os
import logging
from flask_login import login_user, current_user, logout_user, login_required
from marshmallow import ValidationError, validates_schema
# from users.model import User

# Init app
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
# Database
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Init db
db = SQLAlchemy(app)
# Init bcrypt
bcrypt = Bcrypt(app)
# Init ma
ma = Marshmallow(app)

login_manager = LoginManager(app)
login_manager.login_view = 'app.login'
login_manager.login_message_category = 'info'


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


# User Schema
class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'username', 'email', 'password', 'blocked_users')


class RegisterUserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'username', 'email', 'password', 'blocked_users')

    @validates_schema(pass_original=True)
    def validate_numbers(self, _, data, **kwargs):
        user_username = User.query.filter_by(username=data['username']).first()
        if user_username is not None:
            raise ValidationError('User ({}) exists. Please try different username.'.format(data['username']), 'username')

        user_by_email = User.query.filter_by(email=data['email']).first()
        if user_by_email is not None:
            raise ValidationError('Email ({}) has already been in use. Please try different email.'.format(data['email']), 'email')


# Init Schema
user_schema = UserSchema()
users_schema = UserSchema(many=True)
register_user_schema = RegisterUserSchema()


# Create a User
@app.route('/api/register', methods=['POST'])
def register():
    if current_user.is_authenticated:
        return jsonify({'msg': 'You already signed in.'})

    hashed_password = bcrypt.generate_password_hash(request.json['password']).decode('utf-8')
    logging.basicConfig(filename='activatelogs.log', level=logging.DEBUG)
    try:
        data = register_user_schema.load(request.json)
    except ValidationError as err:
        errors = err.messages
        response = {'error': errors}
        logging.error('User cannot be registered due to schema errors.')
        return jsonify(response), 422

    user = User(username=data['username'],
                email=data['email'],
                password=hashed_password,
                blocked_users=data['blocked_users'])
    db.session.add(user)
    db.session.commit()
    logging.info('user has been registered')

    return user_schema.jsonify(user)


# Login
@app.route('/api/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return jsonify({'msg': 'You already signed in.'})

    user = User.query.filter_by(email=request.json['email']).first()
    logging.basicConfig(filename='activatelogs.log', level=logging.DEBUG)
    if user:
        login_user(user, remember=False)
        logging.info('User ({}) logged in.'.format(user.username))
        return jsonify({'msg': 'You signed in successfully.'})
    else:
        logging.error('Login unsuccessful since user is not found.')
        return jsonify({'msg': 'Login unsuccessful.'})


# Logout
@app.route("/api/logout")
def logout():
    logout_user()
    logging.basicConfig(filename='activatelogs.log', level=logging.DEBUG)
    logging.info('User loggout out.')
    return jsonify({'msg': 'You logged out.'})


# Get All Users
@app.route('/api/users', methods=['GET'])
def get_users():
    all_users = User.query.all()
    result = users_schema.dump(all_users)
    return jsonify(result)


# Get Current User
@app.route('/api/current_user', methods=['GET'])
def get_current_user():
    result = user_schema.dump(current_user)
    return jsonify(result)


# Delete User
@app.route('/api/user/<id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get(id)
    username = user.username
    db.session.delete(user)
    db.session.commit()
    logging.basicConfig(filename='activatelogs.log', level=logging.DEBUG)
    logging.info('User ({}) has been deleted.'.format(username))
    return user_schema.jsonify(user)


# Block A User
@app.route('/api/block', methods=['PUT'])
def block_user():
    user_to_be_blocked = User.query.filter_by(username=request.json['username']).first()
    if user_to_be_blocked is None:
        response = {'error': 'User ({}) cannot be found'.format(request.json['username'])}
        return jsonify(response), 422

    if user_to_be_blocked.id not in current_user.blocked_users and request.json['block'] is True:
        current_user.blocked_users = current_user.blocked_users + [user_to_be_blocked.id]
    elif user_to_be_blocked.id in current_user.blocked_users and request.json['block'] is False:
        current_user.blocked_users = [user for user in current_user.blocked_users if user != user_to_be_blocked.id]

    db.session.commit()
    logging.basicConfig(filename='activatelogs.log', level=logging.DEBUG)
    logging.info('User ({}) has been blocked.'.format(user_to_be_blocked.username))
    return user_schema.jsonify(current_user)


# Message Class/Model
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    current_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    message = db.Column(db.String(200))
    messaging_date = db.Column(db.String(100))

    def __init__(self, current_user_id, receiver_user_id, message, messaging_date):
        self.current_user_id = current_user_id
        self.receiver_user_id = receiver_user_id
        self.message = message
        self.messaging_date = messaging_date


# Message Schema
class MessageSchema(ma.Schema):
    class Meta:
        fields = ('id', 'current_user_id', 'receiver_user_id', 'message', 'messaging_date')


class RegisterMessageSchema(ma.Schema):
    class Meta:
        fields = ('id', 'current_user_id', 'receiver_user_id', 'message', 'messaging_date')

    @validates_schema(pass_original=True)
    def validate_numbers(self, _, data, **kwargs):
        if data['receiver_user_id'] in current_user.blocked_users:
            raise ValidationError('User has been blocked. Therefore message cannot be sent.', 'receiver_user_id')


# Init Schema
message_schema = MessageSchema()
messages_schema = MessageSchema(many=True)
register_message_schema = RegisterMessageSchema()

# Create a Message
@app.route('/api/message', methods=['GET', 'POST'])
@login_required
def create_msg():

    recevier_user = User.query.filter_by(username=request.json['username']).first()
    if recevier_user is None:
        response = {'error': 'User ({}) cannot be found'.format(request.json['username'])}
        return jsonify(response), 422

    noew = datetime.now()
    # dd/mm/YY H:M:S
    dt_string = noew.strftime("%d/%m/%Y %H:%M:%S")
    schema_data = {}
    schema_data['messaging_date'] = dt_string
    schema_data['receiver_user_id'] = recevier_user.id
    schema_data['current_user_id'] = current_user.id
    schema_data['message'] = request.json['message']
    logging.basicConfig(filename='activatelogs.log', level=logging.DEBUG)
    try:
        data = register_message_schema.load(schema_data)
    except ValidationError as err:
        errors = err.messages
        response = {'error': errors}
        logging.error('Message cannot be sent.')
        return jsonify(response), 422

    message = Message(current_user_id=current_user.id,
                      receiver_user_id=recevier_user.id,
                      message=data['message'],
                      messaging_date=data['messaging_date'])

    db.session.add(message)
    db.session.commit()
    logging.info('Message has been sent.')

    return message_schema.jsonify(message)


# Delete Message
@app.route('/api/message/<id>', methods=['DELETE'])
def delete_message(id):
    msg = Message.query.get(id)
    db.session.delete(msg)
    db.session.commit()
    logging.basicConfig(filename='activatelogs.log', level=logging.DEBUG)
    logging.info('Message has been deleted.')
    return message_schema.jsonify(msg)


# Get All Messages
@app.route('/api/messages', methods=['GET'])
def get_messages():
    all_msg = Message.query.all()
    result = messages_schema.dump(all_msg)
    return jsonify(result)


# Get Messages From Specific User
# Kullanicilar gecmise donuk mesajlara ulasabilirler
@app.route('/api/messages_from_user/<receiver_id>', methods=['GET'])
def get_messages_from_user(receiver_id):
    all_msg = Message.query.filter_by(current_user_id=current_user.id, receiver_user_id=receiver_id).all()
    result = messages_schema.dump(all_msg)
    return jsonify(result)


# Users which I sent messages
@app.route('/api/mynetwork', methods=['GET'])
def get_mynetwork():
    all_msg = Message.query.filter_by(current_user_id=current_user.id).all()
    receiver_ids = []
    for msg in all_msg:
        if msg.receiver_user_id not in receiver_ids:
            receiver_ids.append(msg.receiver_user_id)

    receivers = []
    for id in receiver_ids:
        receiver = User.query.get(id)
        receivers.append(receiver)

    result = users_schema.dump(receivers)
    return jsonify(result)


# Run Server
if __name__ == '__main__':
    app.run(debug=True)