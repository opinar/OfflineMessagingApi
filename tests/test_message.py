import unittest
import pytest
from app import app as flask_app
import json
from app import Message, User


@pytest.mark.usefixtures("all_messages")
class MessageTestCase(unittest.TestCase):
    def test_create_message(self):
        # Login required
        params = json.dumps({"email": "pinaroz@gmail.com", "password": "password"})
        tester = flask_app.test_client(self)
        tester.post('/api/login', headers={"Content-Type": "application/json"}, data=params)

        # Invalid User
        user = User.query.filter_by(username='wrongusername').first()
        assert user is None

        params_invalid = json.dumps(
            {"username": "wrongusername", "message": "something"})

        res = tester.post('/api/message', headers={"Content-Type": "application/json"}, data=params_invalid)
        assert res.status_code == 500

        # Valid User
        params = json.dumps(
            {"username": "otheruser", "message": "something"})

        response = tester.post('/api/message', headers={"Content-Type": "application/json"}, data=params)
        data = json.loads(response.data)

        assert data['message'] == 'something'

    def test_delete_message(self):
        # Login required
        user_params = json.dumps({"email": "pinaroz@gmail.com", "password": "password"})
        tester = flask_app.test_client(self)
        tester.post('/api/login', headers={"Content-Type": "application/json"}, data=user_params)

        message = Message.query.filter_by(message='hello').first()
        assert message is not None

        tester.delete('/api/message/{}'.format(message.id), content_type='application/json')

        message = Message.query.filter_by(message='hello').first()
        assert message is None

    def test_block_user(self):
        # Login required
        user_params = json.dumps({"email": "pinaroz@gmail.com", "password": "password"})
        tester = flask_app.test_client(self)
        tester.post('/api/login', headers={"Content-Type": "application/json"}, data=user_params)

        # Before Block
        user = User.query.filter_by(username='pinaroz').first()
        assert len(user.blocked_users) == 0

        # After Block
        params = json.dumps({"username": "usertobeblocked", "block": True})
        tester.put('/api/block', headers={"Content-Type": "application/json"}, data=params)

        user = User.query.filter_by(username='pinaroz').first()
        assert len(user.blocked_users) == 1

        # Blocked User tries to send message user (pinaroz)
        params = json.dumps(
            {"username": "usertobeblocked", "message": "how are you?"})

        tester.post('/api/message', headers={"Content-Type": "application/json"}, data=params)

        usertobeblocked = User.query.filter_by(username='usertobeblocked').first()
        # Expecting message is not created
        msg = Message.query.filter_by(current_user_id=usertobeblocked.id, receiver_user_id=user.id, message='how are you?').first()
        assert msg is None
