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
        self.stdout = None
        self.stderr = None

    def run(self):
        command = ["python", "-m", "homework.app.api", "-p", str(SERVER_PORT)]
        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,
        )
        self.stdout, self.stderr = self.process.communicate()

    def stop(self):
        if self.process:
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
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
        if hasattr(cls, "server_thread"):
            if cls.server_thread.stdout:
                print("Server stdout:\n", cls.server_thread.stdout.decode())
            if cls.server_thread.stderr:
                print("Server stderr:\n", cls.server_thread.stderr.decode())

    def test_online_score(self):
        try:
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
            self.assertEqual(response["code"], api.OK)
            self.assertIn("score", response["response"])
            self.assertGreaterEqual(response["response"]["score"], 0)
        except Exception as e:
            print("Произошло исключение:", e)
            if self.server_thread.stderr:
                print("Server stderr:\n", self.server_thread.stderr.decode())
            raise

    def test_clients_interests(self):
        request = {
            "account": "horns&hoofs",
            "login": "h&f",
            "method": "clients_interests",
            "arguments": {"client_ids": [1, 2, 3], "date": "01.01.2020"},
        }
        self.set_valid_auth(request)
        response = self.make_request(request)
        self.assertEqual(response["code"], api.OK)
        self.assertEqual(len(response["response"]), 3)
        for interests in response["response"].values():
            self.assertIsInstance(interests, list)

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
