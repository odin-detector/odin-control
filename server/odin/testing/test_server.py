from nose.tools import *

import requests
import json

from odin.testing.utils import OdinTestServer
from odin import server


class TestOdinServer(OdinTestServer):

    @classmethod
    def setup_class(cls):
        adapter_config = {
            'dummy': {
                'module': 'odin.adapters.dummy.DummyAdapter',
                'test_param': 13.46,
            }
        }
        super(TestOdinServer, cls).setup_class(adapter_config)

    @classmethod
    def teardown_class(cls):
        super(TestOdinServer, cls).teardown_class()

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


class TestOdinServerMissingAdapters(OdinTestServer):

    @classmethod
    def setup_class(cls):
        cls.server_port = 8889
        super(TestOdinServerMissingAdapters, cls).setup_class(None)

    @classmethod
    def teardown_class(cls):
        super(TestOdinServerMissingAdapters, cls).teardown_class()

    def test_server_missing_adapters(self):

        no_adapters_msg_seen = False
        for msg in self.log_warning():
            if msg == 'Failed to resolve API adapters: No adapters specified in configuration':
                no_adapters_msg_seen = True

        assert_true(no_adapters_msg_seen)

if __name__ == '__main__': #pragma: no cover

    import nose
    # If we are running this test module standalone, assume that the ODIN server
    # is already running and disable launching it in the class setup method
    TestOdinServer.launch_server = False
    nose.runmodule()
