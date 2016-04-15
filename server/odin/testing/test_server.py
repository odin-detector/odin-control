from nose.tools import *

import sys
import time
import threading
import requests
import json
from tempfile import NamedTemporaryFile

if sys.version_info[0] == 3:
    from configparser import SafeConfigParser
else:
    from ConfigParser import SafeConfigParser

from tornado.ioloop import IOLoop

from odin import server

class TestOdinServer():

    launch_server = True
    server_host = 'localhost'
    server_port = 8888
    server_api_version = 0.1
    server_thread = None

    @classmethod
    def setup_class(cls):
        if cls.launch_server:

            cls.server_conf_file = NamedTemporaryFile(mode='w+')
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
        return 'http://{}:{}/api/{}/{}'.format(
            self.server_host, self.server_port,
            self.server_api_version, resource)

    def test_simple_client_get(self):
        result = requests.get(self.build_url('dummy/config/none'))
        assert_equal(result.status_code, 200)

    def test_simple_client_put(self):
        headers = {'Content-Type' : 'application/json'}
        payload = {'some': 'data'}
        result = requests.put(self.build_url('dummy/command/execute'),
            data=json.dumps(payload),
            headers=headers)
        assert_equal(result.status_code, 200)

    def test_simple_client_delete(self):
        result = requests.delete(self.build_url('dummy/object/delete'))
        assert_equal(result.status_code, 200)

    def test_bad_api_version(self):
        bad_api_version = 99.9
        temp_api_version = self.server_api_version
        self.server_api_version = bad_api_version
        url = self.build_url('dummy/bad/version')
        self.server_api_version = temp_api_version
        result = requests.get(url)
        assert_equal(result.status_code, 400)
        assert_equal(result.content, 'API version {} is not supported\n'.format(bad_api_version))

    def test_bad_subsystem_adapter(self):
        missing_subsystem = 'missing'
        result = requests.get(self.build_url('{}/object'.format(missing_subsystem)))
        assert_equal(result.status_code, 400)
        assert_equal(result.content, 'No API adapter registered for subsystem {}\n'.format(missing_subsystem))

    def test_api_version(self):
        headers = {'Accept' : 'application/json'}
        result = requests.get(
            'http://{}:{}/api'.format(self.server_host, self.server_port),
            headers=headers
        )
        assert_equal(result.status_code, 200)
        assert_equal(result.json()['api_version'], 0.1)

    def test_api_version_bad_accept(self):
        headers = {'Accept' : 'text/plain'}
        result = requests.get(
            'http://{}:{}/api'.format(self.server_host, self.server_port),
            headers=headers
        )
        assert_equal(result.status_code, 406)

    def test_default_handler(self):

        result = requests.get("http://{}:{}".format(self.server_host, self.server_port))
        assert_equal(result.status_code, 200)

if __name__ == '__main__':

    import nose
    # If we are running this test module standalone, assume that the ODIN server
    # is already running and disable launching it in the class setup method
    TestOdinServer.launch_server = False
    nose.runmodule()
