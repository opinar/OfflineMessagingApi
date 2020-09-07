from flask import Flask, Blueprint, request, jsonify
from flask_login import login_user, current_user, logout_user, login_required
import logging
from app import bcrypt
from app import db
from marshmallow import ValidationError, validate, validates_schema
from users.model import User
from users.schema import register_user_schema, user_schema, users_schema

users = Blueprint('users', __name__, url_prefix='/api/users')


# Create a User
@users.route('/register', methods=['POST'])
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
@users.route('/login', methods=['GET', 'POST'])
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
@users.route("/logout")
def logout():
    logout_user()
    logging.basicConfig(filename='activatelogs.log', level=logging.DEBUG)
    logging.info('User loggout out.')
    return jsonify({'msg': 'You logged out.'})


# Get All Users
@users.route('/users', methods=['GET'])
def get_users():
    all_users = User.query.all()
    result = users_schema.dump(all_users)
    return jsonify(result)


# Get Current User
@users.route('/current_user', methods=['GET'])
def get_current_user():
    result = user_schema.dump(current_user)
    return jsonify(result)


# Delete User
@users.route('/user/<id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get(id)
    username = user.username
    db.session.delete(user)
    db.session.commit()
    logging.basicConfig(filename='activatelogs.log', level=logging.DEBUG)
    logging.info('User ({}) has been deleted.'.format(username))
    return user_schema.jsonify(user)
