import unittest
import pytest
from app import app as flask_app
import json
from app import Message, User


@pytest.mark.usefixtures("all_messages")
class MessageTestCase(unittest.TestCase):
    def test_create_message(self):
        # Login required
        user_params = json.dumps({"email": "pinaroz@gmail.com", "password": "password"})
        tester = flask_app.test_client(self)
        tester.post('/api/login', headers={"Content-Type": "application/json"}, data=user_params)

        params = json.dumps(
            {"username": "wrongusername", "message": "something"})

        response = tester.post('/api/message', headers={"Content-Type": "application/json"}, data=params)
        data = json.loads(response.data)

        assert data['error'] == 'User (wrongusername) cannot be found'

        params = json.dumps(
            {"username": "otheruser", "message": "something"})

        response = tester.post('/api/message', headers={"Content-Type": "application/json"}, data=params)
        data = json.loads(response.data)

        assert data['message'] == 'something'

    def test_delete_message(self):
        message = Message.query.filter_by(message='hello').first()
        assert message is not None
        tester = flask_app.test_client(self)
        tester.delete('/api/message/{}'.format(message.id), content_type='application/json')

        message = Message.query.filter_by(message='hello').first()
        assert message is None

    def test_block_user(self):
        # Login required
        user_params = json.dumps({"email": "pinaroz@gmail.com", "password": "password"})
        tester = flask_app.test_client(self)
        tester.post('/api/login', headers={"Content-Type": "application/json"}, data=user_params)

        user = User.query.filter_by(username='pinaroz').first()
        assert len(user.blocked_users) == 0

        # After Block
        params = json.dumps({"username": "usertobeblocked", "block": True})
        tester.put('/api/block', headers={"Content-Type": "application/json"}, data=params)

        user = User.query.filter_by(username='pinaroz').first()
        assert len(user.blocked_users) == 1

        # Trying to send message to blocked User
        params = json.dumps(
            {"username": "usertobeblocked", "message": "how are you?"})

        response = tester.post('/api/message', headers={"Content-Type": "application/json"}, data=params)
        data = json.loads(response.data)
        assert data['error']['receiver_user_id'][0] == 'User has been blocked. Therefore message cannot be sent.'
