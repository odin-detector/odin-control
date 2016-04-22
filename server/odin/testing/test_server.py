from nose.tools import *

import sys
import time
import threading
import requests
import json
import logging
from tempfile import NamedTemporaryFile

if sys.version_info[0] == 3:  # pragma: no cover
    from configparser import SafeConfigParser
else:                         # pragma: no cover
    from ConfigParser import SafeConfigParser

from tornado.ioloop import IOLoop

from odin import server

def start_server(http_port=8888, with_adapters=True):
    server_conf_file = NamedTemporaryFile(mode='w+')
    parser = SafeConfigParser()

    parser.add_section('server')
    parser.set('server', 'debug_mode', '1')
    parser.set('server', 'http_port', str(http_port))
    parser.set('server', 'http_addr', '127.0.0.1')
    if with_adapters:
        parser.set('server', 'adapters', 'dummy')

    parser.add_section('tornado')
    parser.set('tornado', 'logging', 'debug')

    if with_adapters:
        parser.add_section('adapter.dummy')
        parser.set('adapter.dummy', 'module', 'odin.adapters.dummy.DummyAdapter')

    parser.write(server_conf_file)
    server_conf_file.file.flush()

    server_args = ['--config={}'.format(server_conf_file.name)]
    server_thread = threading.Thread(target=server.main, args=(server_args,))
    server_thread.start()

    return server_thread, server_conf_file


def stop_server(server_thread, server_conf_file):
    if server_thread is not None:
        ioloop = IOLoop.instance()
        ioloop.add_callback(ioloop.stop)
        server_thread.join()

    if server_conf_file is not None:
        server_conf_file.close()


class TestOdinServer():

    launch_server = True
    server_host = 'localhost'
    server_port = 8888
    server_api_version = 0.1
    server_thread = None
    server_conf_file = None

    @classmethod
    def setup_class(cls):
        if cls.launch_server:
            (cls.server_thread, cls.server_conf_file) = start_server()
            time.sleep(0.2)

    @classmethod
    def teardown_class(cls):
        if cls.launch_server:
            stop_server(cls.server_thread, cls.server_conf_file)

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
        assert_equal(result.content.decode('utf-8'), 'API version {} is not supported'.format(bad_api_version))

    def test_bad_subsystem_adapter(self):
        missing_subsystem = 'missing'
        result = requests.get(self.build_url('{}/object'.format(missing_subsystem)))
        assert_equal(result.status_code, 400)
        assert_equal(result.content.decode('utf-8'), 'No API adapter registered for subsystem {}'.format(missing_subsystem))

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
        assert_equal(result.text, 'Requested content types not supported')

    def test_default_handler(self):

        result = requests.get("http://{}:{}".format(self.server_host, self.server_port))
        assert_equal(result.status_code, 200)

    def test_default_accept(self):
        result = requests.get(
            'http://{}:{}/api'.format(self.server_host, self.server_port),
        )

    def test_server_entry_config_error(self):

        server_args = ['--config=absent.cfg']
        rc = server.main((server_args),)
        assert_equal(rc, 2)

class LogCaptureFilter(logging.Filter):

    def __init__(self, *args, **kwargs):

        logging.Filter.__init__(self, *args, **kwargs)
        self.messages = {logging.DEBUG: [],
                         logging.INFO: [],
                         logging.WARNING: [],
                         logging.ERROR: [],
                         logging.CRITICAL: []
                         }

    def filter(self, record):

        self.messages[record.levelno].append(record.getMessage())
        return True

class TestOdinServerMissingAdapters():

    def test_server_missing_adapters(self):

        log_capture_filter = LogCaptureFilter()
        logging.getLogger().handlers[0].addFilter(log_capture_filter)

        (server_thread, server_conf) = start_server(http_port=8889, with_adapters=False)

        time.sleep(0.2)

        no_adapters_msg_seen = False
        for msg in log_capture_filter.messages[logging.WARNING]:
            if msg == 'Failed to resolve API adapters: No adapters specified in configuration':
                no_adapters_msg_seen = True

        assert_true(no_adapters_msg_seen)

        stop_server(server_thread, server_conf)

if __name__ == '__main__': #pragma: no cover

    import nose
    # If we are running this test module standalone, assume that the ODIN server
    # is already running and disable launching it in the class setup method
    TestOdinServer.launch_server = False
    nose.runmodule()
