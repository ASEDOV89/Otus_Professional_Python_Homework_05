import unittest
import subprocess
import time
import requests
import threading
import os
import signal
import json
import hashlib
import datetime
import sys
import logging

# Import the API module
from homework.app import api

# Server configuration
SERVER_PORT = 8080
SERVER_HOST = 'localhost'

# Paths to fixtures
FIXTURES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'fixtures')
REQUEST_FIXTURES_DIR = os.path.join(FIXTURES_DIR, 'requests')
RESPONSE_FIXTURES_DIR = os.path.join(FIXTURES_DIR, 'responses')

# Configure logging to capture server logs
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class ServerThread(threading.Thread):
    """
    Thread class to run the server in the background
    """

    def __init__(self, *args, **kwargs):
        super(ServerThread, self).__init__(*args, **kwargs)
        self.process = None
        self.stdout = ""
        self.stderr = ""

    def run(self):
        # Set environment variables for the server
        env = os.environ.copy()
        env['REDIS_HOST'] = os.getenv('REDIS_HOST', 'localhost')
        env['REDIS_PORT'] = os.getenv('REDIS_PORT', '6379')

        # Command to start the server
        command = ['python', '-m', 'homework.app.api', '-p', str(SERVER_PORT)]
        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            preexec_fn=os.setsid  # To ensure the process group is set so we can kill all processes
        )
        # Give the server time to start
        time.sleep(2)

    def stop(self):
        if self.process:
            # Terminate the server process
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            self.stdout, self.stderr = self.process.communicate()
            self.process.wait()


class TestIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize Redis with test data
        cls.init_redis()

        # Start the server
        cls.server_thread = ServerThread()
        cls.server_thread.start()
        time.sleep(2)  # Ensure server has enough time to start

    @classmethod
    def tearDownClass(cls):
        # Stop the server
        cls.server_thread.stop()
        # Optionally print server logs for debugging
        if cls.server_thread.stdout:
            print("Server stdout:\n", cls.server_thread.stdout.decode())
        if cls.server_thread.stderr:
            print("Server stderr:\n", cls.server_thread.stderr.decode())

    @staticmethod
    def init_redis():
        """
        Initialize Redis with test data.
        """
        import redis

        REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
        REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))

        client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

        # Add test data to Redis
        client.set('i:1', json.dumps(["books", "music"]))
        client.set('i:2', json.dumps(["travel", "sports"]))
        client.set('i:3', json.dumps(["movies", "tech"]))

    def load_fixture(self, fixture_type, filename):
        """
        Load a fixture file.
        """
        if fixture_type == 'request':
            fixture_path = os.path.join(REQUEST_FIXTURES_DIR, filename)
        elif fixture_type == 'response':
            fixture_path = os.path.join(RESPONSE_FIXTURES_DIR, filename)
        else:
            raise ValueError("Invalid fixture type. Use 'request' or 'response'.")

        with open(fixture_path, 'r') as f:
            return json.load(f)

    def set_valid_auth(self, request):
        """
        Set valid authentication token for the request.
        """
        if request.get("login") == api.ADMIN_LOGIN:
            request["token"] = hashlib.sha512(
                (datetime.datetime.now().strftime("%Y%m%d%H") + api.ADMIN_SALT).encode("utf-8")
            ).hexdigest()
        else:
            msg = (
                    request.get("account", "") +
                    request.get("login", "") + api.SALT
            ).encode("utf-8")
            request["token"] = hashlib.sha512(msg).hexdigest()

    def make_request(self, request):
        """
        Send a POST request to the server.
        """
        url = f'http://{SERVER_HOST}:{SERVER_PORT}/method'
        headers = {'Content-Type': 'application/json'}
        response = requests.post(
            url, data=json.dumps(request), headers=headers)
        return response.json()

    def test_valid_online_score(self):
        """
        Test the valid online_score request.
        """
        request_data = self.load_fixture('request', 'valid_online_score_request.json')
        expected_response = self.load_fixture('response', 'expected_online_score_response.json')

        # Set valid authentication token
        self.set_valid_auth(request_data)

        # Send the request
        response = self.make_request(request_data)

        # Check the response
        self.assertEqual(response['code'], expected_response['code'])
        self.assertIn('score', response['response'])
        self.assertGreaterEqual(response['response']['score'], 0)

    def test_invalid_online_score(self):
        """
        Test the invalid online_score request.
        """
        request_data = self.load_fixture('request', 'invalid_online_score_request.json')

        # Set valid authentication token
        self.set_valid_auth(request_data)

        # Send the request
        response = self.make_request(request_data)

        # Check error code
        self.assertNotEqual(response['code'], api.OK)
        self.assertIn('error', response)

    def test_valid_clients_interests(self):
        """
        Test the valid clients_interests request.
        """
        request_data = self.load_fixture('request', 'valid_clients_interests_request.json')
        expected_response = self.load_fixture('response', 'expected_clients_interests_response.json')

        # Set valid authentication token
        self.set_valid_auth(request_data)

        # Send the request
        response = self.make_request(request_data)

        # Check the response
        self.assertEqual(response['code'], expected_response['code'])
        self.assertEqual(len(response['response']), len(expected_response['response']))
        for cid, interests in response['response'].items():
            self.assertIn(cid, expected_response['response'])
            self.assertEqual(interests, expected_response['response'][cid])

    def test_invalid_clients_interests(self):
        """
        Test the invalid clients_interests request.
        """
        request_data = self.load_fixture('request', 'invalid_clients_interests_request.json')

        # Set valid authentication token
        self.set_valid_auth(request_data)

        # Send the request
        response = self.make_request(request_data)

        # Check error code
        self.assertNotEqual(response['code'], api.OK)
        self.assertIn('error', response)

    # Additional test cases can be added following the same pattern


if __name__ == '__main__':
    unittest.main()





# import unittest
# import subprocess
# import time
# import requests
# import threading
# import os
# import signal
# import json
# import hashlib
# import datetime
# from homework.app import api
#
# SERVER_PORT = 8080
# SERVER_HOST = "localhost"
#
#
# class ServerThread(threading.Thread):
#     def __init__(self, *args, **kwargs):
#         super(ServerThread, self).__init__(*args, **kwargs)
#         self.process = None
#         self.stdout = ""
#         self.stderr = ""
#
#     def run(self):
#         env = os.environ.copy()
#         env['REDIS_HOST'] = os.getenv('REDIS_HOST', 'localhost')  # Используем значение из переменной окружения или по умолчанию
#         command = ['python', '-m', 'homework.app.api', '-p', str(SERVER_PORT)]
#         self.process = subprocess.Popen(
#             command,
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE,
#             preexec_fn=os.setsid,
#             env=env
#         )
#
#         time.sleep(2)
#
#     def stop(self):
#         if self.process:
#             os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
#             self.stdout, self.stderr = self.process.communicate()
#             self.process.wait()
#
#
# class TestIntegration(unittest.TestCase):
#     @classmethod
#     def setUpClass(cls):
#         cls.server_thread = ServerThread()
#         cls.server_thread.start()
#         time.sleep(2)
#
#     @classmethod
#     def tearDownClass(cls):
#         cls.server_thread.stop()
#         if cls.server_thread.stdout:
#             print("Server stdout:\n", cls.server_thread.stdout)
#         if cls.server_thread.stderr:
#             print("Server stderr:\n", cls.server_thread.stderr)
#
#     def test_online_score(self):
#         request = {
#             "account": "horns&hoofs",
#             "login": "h&f",
#             "method": "online_score",
#             "arguments": {
#                 "phone": "71234567890",
#                 "email": "test@example.com",
#                 "first_name": "John",
#                 "last_name": "Doe",
#                 "birthday": "01.01.1990",
#                 "gender": 1,
#             },
#         }
#         self.set_valid_auth(request)
#         response = self.make_request(request)
#
#         if response["code"] != api.OK:
#             print("Server responded with error code:", response["code"])
#             print("Server response:", response)
#             if self.server_thread.stderr:
#                 print("Server stderr:\n", self.server_thread.stderr)
#         self.assertEqual(response["code"], api.OK)
#
#     def test_clients_interests(self):
#         request = {
#             "account": "horns&hoofs",
#             "login": "h&f",
#             "method": "clients_interests",
#             "arguments": {"client_ids": [1, 2, 3], "date": "01.01.2020"},
#         }
#         self.set_valid_auth(request)
#         response = self.make_request(request)
#         if response["code"] != api.OK:
#             print("Server responded with error code:", response["code"])
#             print("Server response:", response)
#             if self.server_thread.stderr:
#                 print("Server stderr:\n", self.server_thread.stderr.decode())
#             else:
#                 print("No stderr captured from server.")
#         self.assertEqual(response["code"], api.OK)
#
#     def make_request(self, request):
#         url = f"http://{SERVER_HOST}:{SERVER_PORT}/method"
#         headers = {"Content-Type": "application/json"}
#         response = requests.post(url, data=json.dumps(request), headers=headers)
#         return response.json()
#
#     def set_valid_auth(self, request):
#         if request.get("login") == api.ADMIN_LOGIN:
#             request["token"] = hashlib.sha512(
#                 (datetime.datetime.now().strftime("%Y%m%d%H") + api.ADMIN_SALT).encode(
#                     "utf-8"
#                 )
#             ).hexdigest()
#         else:
#             msg = (
#                 request.get("account", "") + request.get("login", "") + api.SALT
#             ).encode("utf-8")
#             request["token"] = hashlib.sha512(msg).hexdigest()
#
#
# if __name__ == "__main__":
#     unittest.main()
