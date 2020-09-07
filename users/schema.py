from app import ma
from marshmallow import ValidationError, validates_schema
from models.user import User


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
