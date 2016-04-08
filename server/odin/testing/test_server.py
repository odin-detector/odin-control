from nose.tools import *

import threading
import requests
import json
from tornado.ioloop import IOLoop

from odin import server

class TestOdinServer():

    launch_server = True
    server_host = "localhost"
    server_port = 8888
    server_api_version = 0.1
    server_thread = None

    @classmethod
    def setup_class(cls):
        if cls.launch_server:
            cls.server_thread = threading.Thread(target=server.main)
            cls.server_thread.start()

    @classmethod
    def teardown_class(cls):
        if cls.server_thread != None:
            ioloop = IOLoop.instance()
            ioloop.add_callback(ioloop.stop)
            cls.server_thread.join()

    def build_url(self, resource):
        return "http://{}:{}/api/{}/{}".format(
            self.server_host, self.server_port,
            self.server_api_version, resource)

    def test_simple_client(self):
        result = requests.put(self.build_url("dummy/command/execute"))
        assert_equal(result.status_code, 200)

    def test_api_version(self):
        result = requests.get("http://{}:{}/api".format(
            self.server_host, self.server_port
        ))



if __name__ == '__main__':

    import nose
    # If we are running this test module standalone, assume that the ODIN server
    # is already running and disable launching it in the class setup method
    TestOdinServer.launch_server = False
    nose.runmodule()
