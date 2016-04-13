from nose.tools import *

import time
import threading
import requests
import json
from tempfile import NamedTemporaryFile
from ConfigParser import SafeConfigParser

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

            cls.server_conf_file = NamedTemporaryFile()
            parser = SafeConfigParser()

            parser.add_section('server')
            parser.set('server', 'debug_mode', '1')
            parser.set('server', 'http_port', '8888')
            parser.set('server', 'http_addr', '127.0.0.1')
            parser.set('server', 'adapters', 'dummy')

            parser.add_section('tornado')
            parser.set('tornado', 'logging', 'debug')

            parser.add_section('adapter.dummy')
            parser.set('adapter.dummy', 'module', 'odin.adapters.dummy.DummyAdapter')

            parser.write(cls.server_conf_file)
            cls.server_conf_file.file.flush()


            server_args=['--config={}'.format(cls.server_conf_file.name)]
            cls.server_thread = threading.Thread(target=server.main, args=(server_args,))
            cls.server_thread.start()
            time.sleep(0.2)

    @classmethod
    def teardown_class(cls):
        if cls.server_thread != None:
            ioloop = IOLoop.instance()
            ioloop.add_callback(ioloop.stop)
            cls.server_thread.join()
        cls.server_conf_file.close()

    def build_url(self, resource):
        return "http://{}:{}/api/{}/{}".format(
            self.server_host, self.server_port,
            self.server_api_version, resource)

    def test_simple_client(self):
        headers = {'Content-Type' : 'application/json'}
        payload = {'some': 'data'}
        result = requests.put(self.build_url("dummy/command/execute"),
            data=json.dumps(payload),
            headers=headers)
        assert_equal(result.status_code, 200)

    def test_api_version(self):
        headers = {'Accept' : 'application/json'}
        result = requests.get(
            "http://{}:{}/api".format(self.server_host, self.server_port),
            headers=headers
        )
        assert_equal(result.status_code, 200)
        assert_equal(result.json()['api_version'], 0.1)

    def test_api_version_bad_accept(self):
        headers = {'Accept' : 'text/plain'}
        result = requests.get(
            "http://{}:{}/api".format(self.server_host, self.server_port),
            headers=headers
        )
        assert_equal(result.status_code, 406)

if __name__ == '__main__':

    import nose
    # If we are running this test module standalone, assume that the ODIN server
    # is already running and disable launching it in the class setup method
    TestOdinServer.launch_server = False
    nose.runmodule()
