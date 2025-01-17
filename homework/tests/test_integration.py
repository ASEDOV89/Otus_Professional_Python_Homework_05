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
from homework.app import api

SERVER_PORT = 8080
SERVER_HOST = "localhost"


class ServerThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(ServerThread, self).__init__(*args, **kwargs)
        self.process = None
        self.stdout = ""
        self.stderr = ""

    def run(self):
        env = os.environ.copy()
        env['REDIS_HOST'] = os.getenv('REDIS_HOST', 'localhost')  # Используем значение из переменной окружения или по умолчанию
        command = ['python', '-m', 'homework.app.api', '-p', str(SERVER_PORT)]
        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,
            env=env
        )

        time.sleep(2)

    def stop(self):
        if self.process:
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            self.stdout, self.stderr = self.process.communicate()
            self.process.wait()


class TestIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server_thread = ServerThread()
        cls.server_thread.start()
        time.sleep(2)

    @classmethod
    def tearDownClass(cls):
        cls.server_thread.stop()
        if cls.server_thread.stdout:
            print("Server stdout:\n", cls.server_thread.stdout)
        if cls.server_thread.stderr:
            print("Server stderr:\n", cls.server_thread.stderr)

    def test_online_score(self):
        request = {
            "account": "horns&hoofs",
            "login": "h&f",
            "method": "online_score",
            "arguments": {
                "phone": "71234567890",
                "email": "test@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "birthday": "01.01.1990",
                "gender": 1,
            },
        }
        self.set_valid_auth(request)
        response = self.make_request(request)

        if response["code"] != api.OK:
            print("Server responded with error code:", response["code"])
            print("Server response:", response)
            if self.server_thread.stderr:
                print("Server stderr:\n", self.server_thread.stderr)
        self.assertEqual(response["code"], api.OK)

    def test_clients_interests(self):
        request = {
            "account": "horns&hoofs",
            "login": "h&f",
            "method": "clients_interests",
            "arguments": {"client_ids": [1, 2, 3], "date": "01.01.2020"},
        }
        self.set_valid_auth(request)
        response = self.make_request(request)
        if response["code"] != api.OK:
            print("Server responded with error code:", response["code"])
            print("Server response:", response)
            if self.server_thread.stderr:
                print("Server stderr:\n", self.server_thread.stderr.decode())
            else:
                print("No stderr captured from server.")
        self.assertEqual(response["code"], api.OK)

    def make_request(self, request):
        url = f"http://{SERVER_HOST}:{SERVER_PORT}/method"
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, data=json.dumps(request), headers=headers)
        return response.json()

    def set_valid_auth(self, request):
        if request.get("login") == api.ADMIN_LOGIN:
            request["token"] = hashlib.sha512(
                (datetime.datetime.now().strftime("%Y%m%d%H") + api.ADMIN_SALT).encode(
                    "utf-8"
                )
            ).hexdigest()
        else:
            msg = (
                request.get("account", "") + request.get("login", "") + api.SALT
            ).encode("utf-8")
            request["token"] = hashlib.sha512(msg).hexdigest()


if __name__ == "__main__":
    unittest.main()
