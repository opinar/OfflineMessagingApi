import unittest
import pytest
from app import app as flask_app
import json
from app import User


@pytest.mark.usefixtures("all_users")
class UserTestCase(unittest.TestCase):
    def test_register(self):
        user = User.query.filter_by(username='newuser').first()
        assert user is None

        num_of_allusers = User.query.count()

        params = json.dumps(
            {"username": "newuser",
             "password": "password",
             "email": "newuser@gmail.com",
             "blocked_users": []
             })

        tester = flask_app.test_client(self)
        response = tester.post('/api/register', headers={"Content-Type": "application/json"}, data=params)
        data = json.loads(response.data)
        assert data['username'] == 'newuser'
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert User.query.count() == num_of_allusers + 1

    def test_logout(self):
        tester = flask_app.test_client(self)
        response = tester.get('/api/logout')
        data = json.loads(response.data)
        assert data['msg'] == "You logged out."

    def test_login(self):
        params = json.dumps({"email": "pinaroz@gmail.com", "password": "password"})
        tester = flask_app.test_client(self)
        response = tester.post('/api/login', headers={"Content-Type": "application/json"}, data=params)
        data = json.loads(response.data)
        assert data['msg'] == "You signed in successfully."

    def test_get_all_users(self):
        tester = flask_app.test_client(self)
        response = tester.get('/api/users', content_type='application/json')
        data = json.loads(response.data)

        self.assertEqual(len(data), 3)

    def test_delete_user(self):
        # Login required
        params = json.dumps({"email": "pinaroz@gmail.com", "password": "password"})
        tester = flask_app.test_client(self)
        tester.post('/api/login', headers={"Content-Type": "application/json"}, data=params)

        user = User.query.filter_by(username='pinaroz').first()
        assert user is not None

        tester.delete('/api/user/{}'.format(user.id), content_type='application/json')

        user = User.query.filter_by(username='pinaroz').first()
        assert user is None
