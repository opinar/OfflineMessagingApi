import pytest
from app import db
import os
from flask import Flask
from app import Message
from app import User


@pytest.yield_fixture(scope='session')
def app():
    """
    Setup our flask test app, this only gets executed once.

   :return: Flask app
    """
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_uri = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
    if '_test' not in 'sqlite:///' + os.path.join(basedir, 'db.sqlite'):
        db_uri = '{0}_test'.format('sqlite:///' + os.path.join(basedir, 'db.sqlite'))

    params = {
        'DEBUG': False,
        'TESTING': True,
        'APM_ACTIVE': False,
        'CELERY_ALWAYS_EAGER': True,
        'LOG_LEVEL': 'DEBUG',
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_DATABASE_URI': db_uri,
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    }

    _app = Flask(__name__, instance_relative_config=True)
    _app.config.update(params)

    # Establish an application context before running the tests.
    ctx = _app.app_context()
    ctx.push()

    yield _app

    ctx.pop()


@pytest.yield_fixture(scope='function')
def client(app):
    """
    Setup an app client, this gets executed for each test function.

   :param app: Pytest fixture
   :return: Flask app client
    """
    yield app.test_client()


@pytest.fixture(scope="class")
def all_messages():
    db.session.query(Message).delete()
    db.session.commit()

    messages = [
        {
            "current_user_id": 8,
            "message": "hello",
            "messaging_date": "05/09/2020 13:46:49",
            "receiver_user_id": 5
        },
        {
            "current_user_id": 8,
            "message": "bye",
            "messaging_date": "05/09/2020 15:30:50",
            "receiver_user_id": 5
        }
    ]

    for msg in messages:
        db.session.add(Message(**msg))
    db.session.commit()

    return db


@pytest.fixture()
def all_users():
    db.session.query(User).delete()
    db.session.commit()

    users = [
        {
            "username": 'pinaroz',
            "email": "pinaroz@gmail.com",
            "password": "password",
            "blocked_users": []
        },
        {
            "username": 'otheruser',
            "email": "otheruser@gmail.com",
            "password": "password",
            "blocked_users": []
        },
        {
            "username": 'usertobeblocked',
            "email": "usertobeblocked@gmail.com",
            "password": "password",
            "blocked_users": []
        }
    ]

    for us in users:
        db.session.add(User(**us))
    db.session.commit()

    return db
