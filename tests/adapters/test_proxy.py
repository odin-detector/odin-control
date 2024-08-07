""" Unit tests for the ODIN ProxyAdapter.

Tim Nicholls, STFC Application Engineering Group.
"""

import sys
import builtins
import threading
import logging
import time
from io import StringIO

import pytest

import requests

from tornado.testing import bind_unused_port
from tornado.ioloop import IOLoop
from tornado.httpclient import HTTPResponse
from tornado.web import Application, RequestHandler
from tornado.httpserver import HTTPServer
import tornado.gen

from odin.adapters.proxy import ProxyTarget, ProxyAdapter
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from odin.adapters.adapter import wants_metadata
from odin.util import convert_unicode_to_string
from tests.utils import log_message_seen

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock, patch
    import asyncio
else:                         # pragma: no cover
    from mock import Mock, patch


class ProxyTestHandler(RequestHandler):
    """ Tornado request handler for use in test server needed for proxy tests."""

    # Data structure served by request handler
    data = {
        'one': (1, None),  # this allows for auto generated metadata for testing purposes
        'two': 2.0,
        'pi': 3.14,
        'more':
        {
            'three': 3.0,
            'replace': 'Replace Me!',
            'even_more': {
                'extra_val': 5.5
            }
        }
    }
    param_tree = ParameterTree(data)

    def initialize(self, server):
        """Increment the server access count every time the request handler is invoked."""
        server.access_count += 1

    def get(self, path=''):
        """Handle GET requests to the test server."""
        try:
            data_ref = self.param_tree.get(path, wants_metadata(self.request))
            self.write(data_ref)
        except ParameterTreeError:
            self.set_status(404)
            self.write_error(404)
        except Exception as other_e:
            logging.error("ProxyTestHandler GET failed: %s", str(other_e))
            self.write_error(500)

    def put(self, path):
        """Handle PUT requests to the test server."""
        response_body = convert_unicode_to_string(tornado.escape.json_decode(self.request.body))
        try:
            self.param_tree.set(path, response_body)
            data_ref = self.param_tree.get(path)

            self.write(data_ref)
        except ParameterTreeError:
            self.set_status(404)
            self.write_error(404)
        except Exception as other_e:
            logging.error("ProxyTestHandler PUT failed: %s", str(other_e))
            self.write_error(500)


class ProxyTestServer(object):
    """ Tornado test server for use in proxy testing."""
    def __init__(self,):
        """Initialise the server."""
        self.access_count = 0
        self.server_event_loop = None

        self.server_thread = threading.Thread(target=self._run_server)
        self.server_thread.start()
        time.sleep(0.2)

    def _run_server(self):

        if sys.version_info[0] == 3:
            asyncio.set_event_loop(asyncio.new_event_loop())

        self.server_event_loop = IOLoop()

        self.sock, self.port = bind_unused_port()
        self.app = Application([('/(.*)', ProxyTestHandler, dict(server=self))])
        self.server = HTTPServer(self.app)
        self.server.add_socket(self.sock)

        self.server_event_loop.start()

    def stop(self):
        """Stop the server, using a callback added to the server IOLoop."""

        if self.server_thread is not None:
            self.server_event_loop.add_callback(self.server_event_loop.stop)
            self.server_thread.join()
            self.server_thread = None
            self.server.stop()

    def get_access_count(self):
        """Return the server access count."""
        return self.access_count

    def clear_access_count(self):
        """Clear the server access count."""
        self.access_count = 0


class ProxyTargetTestFixture(object):
    """Container class used in fixtures for testing ProxyTarget."""
    def __init__(self, proxy_target_cls):
        """Initialise the fixture, starting the test server and defining a target."""
        self.test_server = ProxyTestServer()
        self.port = self.test_server.port

        self.name = 'test_target'
        self.url = 'http://127.0.0.1:{}/'.format(self.port)
        self.request_timeout = 0.1

        self.proxy_target = proxy_target_cls(self.name, self.url, self.request_timeout)

    def __del__(self):
        """Ensure test server is stopped on deletion."""
        self.stop()

    def stop(self):
        """Stop the test server and proxy HTTP client."""
        self.test_server.stop()


@pytest.fixture()
def test_proxy_target():
    """Fixture used in ProxyTarget test cases."""
    test_proxy_target = ProxyTargetTestFixture(ProxyTarget)
    yield test_proxy_target
    test_proxy_target.stop()


class TestProxyTarget():
    """Test cases for the ProxyTarget class."""

    def test_proxy_target_init(self, test_proxy_target):
        """Test the proxy tartget is correctly initialised."""
        assert test_proxy_target.proxy_target.name == test_proxy_target.name
        assert test_proxy_target.proxy_target.url == test_proxy_target.url
        assert test_proxy_target.proxy_target.request_timeout == test_proxy_target.request_timeout

    def test_proxy_target_remote_get(self, test_proxy_target):
        """Test the that remote GET to a proxy target succeeds."""
        test_proxy_target.proxy_target.last_update = ''

        test_proxy_target.proxy_target.remote_get()
        assert test_proxy_target.proxy_target.data == ProxyTestHandler.param_tree.get("")
        assert test_proxy_target.proxy_target.status_code == 200
        assert test_proxy_target.proxy_target.last_update != ''

    def test_param_tree_get(self, test_proxy_target):
        """Test that a proxy target get returns a parameter tree."""
        param_tree = test_proxy_target.proxy_target.status_param_tree.get('')
        for tree_element in ['url', 'status_code', 'error', 'last_update']:
            assert tree_element in param_tree

    def test_proxy_target_http_get_error_404(self, test_proxy_target):
        """Test that a proxy target GET to a bad URL returns a 404 not found error."""
        bad_url = test_proxy_target.url + 'notfound/'
        proxy_target = ProxyTarget(test_proxy_target.name, bad_url,
                                   test_proxy_target.request_timeout)
        proxy_target.remote_get('notfound')

        assert proxy_target.status_code == 404
        assert 'Not Found' in proxy_target.error_string

    def test_proxy_target_timeout_error(self, test_proxy_target):
        """Test that a proxy target GET request that times out is handled correctly"""
        proxy_target = ProxyTarget(test_proxy_target.name, test_proxy_target.url,
                                   test_proxy_target.request_timeout)

        with patch('requests.request') as request_mock:
            request_mock.side_effect = requests.exceptions.Timeout('timeout')
            proxy_target.remote_get()

        assert proxy_target.status_code == 408
        assert 'timeout' in proxy_target.error_string

    def test_proxy_target_io_error(self, test_proxy_target):
        """Test that a proxy target GET request to a non-existing server returns a 502 error."""
        bad_url = 'http://127.0.0.1:{}'.format(test_proxy_target.port + 1)
        proxy_target = ProxyTarget(test_proxy_target.name, bad_url,
                                   test_proxy_target.request_timeout)
        proxy_target.remote_get()

        assert proxy_target.status_code == 502
        assert 'Connection refused' in proxy_target.error_string

    def test_proxy_target_unknown_error(self, test_proxy_target):
        """Test that a proxy target GET request handles an unknown exception returning a 500 error."""
        proxy_target = ProxyTarget(
            test_proxy_target.name, test_proxy_target.url, test_proxy_target.request_timeout
        )

        with patch('requests.request') as request_mock:
            request_mock.side_effect = ValueError('value error')
            proxy_target.remote_get()

        assert proxy_target.status_code == 500
        assert 'value error' in proxy_target.error_string

    def test_proxy_target_traps_decode_error(self, test_proxy_target):
        """Test that a proxy target correctly traps errors decoding a non-JSON response body."""

        proxy_target = ProxyTarget(
            test_proxy_target.name, test_proxy_target.url, test_proxy_target.request_timeout
        )

        with patch('requests.request') as request_mock:

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b'wibble'
            request_mock.return_value = mock_response
            proxy_target.remote_get()

        assert proxy_target.status_code == 415
        assert "Failed to decode response body" in proxy_target.error_string

class ProxyAdapterTestFixture():
    """Container class used in fixtures for testing proxy adapters."""

    def __init__(self):
        """Initliase the fixture, setting up the ProxyAdapter with the correct configuration."""
        self.num_targets = 2

        self.test_servers = []
        self.ports = []
        self.target_config = ""

        # Launch the appropriate number of target test servers.""""
        for _ in range(self.num_targets):

            test_server = ProxyTestServer()
            self.test_servers.append(test_server)
            self.ports.append(test_server.port)

        self.target_config = ','.join([
            "node_{}=http://127.0.0.1:{}/".format(tgt, port) for (tgt, port) in enumerate(self.ports)
        ])

        self.adapter_kwargs = {
            'targets': self.target_config,
            'request_timeout': 1.0,
        }
        self.adapter = ProxyAdapter(**self.adapter_kwargs)

        self.path = ''
        self.request = Mock()
        self.request.headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        self.request.body = '{"pi":2.56}'

    def __del__(self):
        """Ensure the test servers are stopped on deletion."""
        self.stop()

    def stop(self):
        """Stop the proxied test servers, ensuring any client connections to them are closed."""
        for test_server in self.test_servers:
            test_server.stop()

    def clear_access_counts(self):
        """Clear the access counters in all test servers."""
        for test_server in self.test_servers:
            test_server.clear_access_count()


@pytest.fixture(scope="class")
def proxy_adapter_test():
    """Fixture used in testing the ProxyAdapter class."""
    proxy_adapter_test = ProxyAdapterTestFixture()
    yield proxy_adapter_test

    proxy_adapter_test.stop()


real_import = builtins.__import__
def monkey_import_importerror(name, globals=None, locals=None, fromlist=(), level=0):
    """Monkey patch method simulating import error for the requests library"""
    if name in ('requests', ):
        raise ImportError("{} not found".format(name))
    return real_import(name, globals=globals, locals=locals, fromlist=fromlist, level=level)

class TestProxyAdapter():
    """Test cases for testing the ProxyAdapter class."""

    def test_requests_missing(self, monkeypatch):
        """
        Test that the proxy adapter module raises an import error with a specific message when the
        requests package is not installed.
        """
        monkeypatch.delitem(sys.modules, 'requests', raising=False)
        monkeypatch.delitem(sys.modules, 'odin.adapters.proxy')
        monkeypatch.setattr(builtins, '__import__', monkey_import_importerror)

        with pytest.raises(ImportError) as excinfo:
            from odin.adapters.proxy import ProxyAdapter

        assert("requests package not installed" in str(excinfo.value))

    def test_adapter_loaded(self, proxy_adapter_test):
        """Test that the proxy adapter is loaded and configured correctly."""
        assert len(proxy_adapter_test.adapter.targets) == proxy_adapter_test.num_targets

    def test_adapter_get(self, proxy_adapter_test):
        """
        Test that a GET request to the proxy adapter returns the appropriate data for all
        defined proxied targets.
        """
        response = proxy_adapter_test.adapter.get(
            proxy_adapter_test.path, proxy_adapter_test.request)

        assert 'status' in response.data

        assert len(response.data) == proxy_adapter_test.num_targets + 1

        for tgt in range(proxy_adapter_test.num_targets):
            node_str = 'node_{}'.format(tgt)
            assert node_str in response.data
            assert response.data[node_str], ProxyTestHandler.data

    def test_adapter_get_metadata(self, proxy_adapter_test):
        request = proxy_adapter_test.request
        request.headers['Accept'] = "{};{}".format(request.headers['Accept'], "metadata=True")
        response = proxy_adapter_test.adapter.get(proxy_adapter_test.path, request)

        assert "status" in response.data
        for target in range(proxy_adapter_test.num_targets):
            node_str = 'node_{}'.format(target)
            assert node_str in response.data
            assert "one" in response.data[node_str]
            assert "type" in response.data[node_str]['one']

    def test_adapter_get_status_metadata(self, proxy_adapter_test):
        request = proxy_adapter_test.request
        request.headers['Accept'] = "{};{}".format(request.headers['Accept'], "metadata=True")
        response = proxy_adapter_test.adapter.get(proxy_adapter_test.path, request)

        assert 'status' in response.data
        assert 'node_0' in response.data['status']
        assert 'type' in response.data['status']['node_0']['error']

    def test_adapter_put(self, proxy_adapter_test):
        """
        Test that a PUT request to the proxy adapter returns the appropriate data for all
        defined proxied targets.
        """
        response = proxy_adapter_test.adapter.put(
            proxy_adapter_test.path, proxy_adapter_test.request)

        assert 'status' in response.data

        assert len(response.data) == proxy_adapter_test.num_targets + 1

        for tgt in range(proxy_adapter_test.num_targets):
            node_str = 'node_{}'.format(tgt)
            assert node_str in response.data
            assert convert_unicode_to_string(response.data[node_str]) == ProxyTestHandler.param_tree.get("")

    def test_adapter_get_proxy_path(self, proxy_adapter_test):
        """Test that a GET to a sub-path within a targer succeeds and return the correct data."""
        node = proxy_adapter_test.adapter.targets[0].name
        path = "more/even_more"
        response = proxy_adapter_test.adapter.get(
            "{}/{}".format(node, path), proxy_adapter_test.request)

        assert response.data["even_more"] == ProxyTestHandler.data["more"]["even_more"]
        assert proxy_adapter_test.adapter.param_tree.get('')['status'][node]['status_code'] == 200

    def test_adapter_get_proxy_path_trailing_slash(self, proxy_adapter_test):
        """
        Test that a PUT to a sub-path with a trailing slash in the URL within a targer succeeds
        and returns the correct data.
        """
        node = proxy_adapter_test.adapter.targets[0].name
        path = "more/even_more/"
        response = proxy_adapter_test.adapter.get(
            "{}/{}".format(node, path), proxy_adapter_test.request)

        assert response.data["even_more"] == ProxyTestHandler.data["more"]["even_more"]
        assert proxy_adapter_test.adapter.param_tree.get('')['status'][node]['status_code'] == 200

    def test_adapter_put_proxy_path(self, proxy_adapter_test):
        """
        Test that a PUT to a sub-path without a trailing slash in the URL within a targer succeeds
        and returns the correct data.
        """
        node = proxy_adapter_test.adapter.targets[0].name
        path = "more"
        proxy_adapter_test.request.body = '{"replace": "been replaced"}'
        response = proxy_adapter_test.adapter.put(
            "{}/{}".format(node, path), proxy_adapter_test.request)

        logging.debug("Response: %s", response.data)
        assert proxy_adapter_test.adapter.param_tree.get('')['status'][node]['status_code'] == 200
        assert convert_unicode_to_string(response.data["more"]["replace"]) == "been replaced"

    def test_adapter_get_bad_path(self, proxy_adapter_test):
        """Test that a GET to a bad path within a target returns the appropriate error."""
        missing_path = 'missing/path'
        response = proxy_adapter_test.adapter.get(missing_path, proxy_adapter_test.request)

        assert 'error' in response.data
        assert 'Invalid path: {}'.format(missing_path) == response.data['error']

    def test_adapter_put_bad_path(self, proxy_adapter_test):
        """Test that a PUT to a bad path within a target returns the appropriate error."""
        missing_path = 'missing/path'
        response = proxy_adapter_test.adapter.put(missing_path, proxy_adapter_test.request)

        assert 'error' in response.data
        assert 'Invalid path: {}'.format(missing_path) == response.data['error']

    def test_adapter_put_bad_type(self, proxy_adapter_test):
        """Test that a PUT request with an inappropriate type returns the appropriate error."""
        proxy_adapter_test.request.body = "bad_body"
        response = proxy_adapter_test.adapter.put(
            proxy_adapter_test.path, proxy_adapter_test.request)

        assert 'error' in response.data
        assert 'Failed to decode PUT request body:' in response.data['error']

    def test_adapter_bad_timeout(self, proxy_adapter_test, caplog):
        """Test that a bad timeout specified for the proxy adatper yields a logged error message."""
        bad_timeout = 'not_timeout'
        _ = ProxyAdapter(request_timeout=bad_timeout)

        assert log_message_seen(caplog, logging.ERROR,
            'Illegal timeout specified for proxy adapter: {}'.format(bad_timeout))

    def test_adapter_bad_target_spec(self, proxy_adapter_test, caplog):
        """
        Test that an incorrectly formatted target specified passed to a proxy adapter yields a
        logged error message.
        """
        bad_target_spec = 'bad_target_1,bad_target_2'
        _ = ProxyAdapter(targets=bad_target_spec)

        assert log_message_seen(caplog, logging.ERROR,
            "Illegal target specification for proxy adapter: bad_target_1")

    def test_adapter_no_target_spec(self, caplog):
        """
        Test that a proxy adapter instantiated with no target specifier yields a logged
        error message.
        """
        _ = ProxyAdapter()

        assert log_message_seen(caplog, logging.ERROR,
            "Failed to resolve targets for proxy adapter")

    def test_adapter_get_access_count(self, proxy_adapter_test):
        """
        Test that requests via the proxy adapter correctly increment the access counters in the
        target test servers.
        """
        proxy_adapter_test.clear_access_counts()

        _ = proxy_adapter_test.adapter.get(proxy_adapter_test.path, proxy_adapter_test.request)

        access_counts = [server.get_access_count() for server in proxy_adapter_test.test_servers]
        assert access_counts == [1]*proxy_adapter_test.num_targets

    def test_adapter_counter_get_single_node(self, proxy_adapter_test):
        """
        Test that a requested to a single target in the proxy adapter only accesses that target,
        increasing the access count appropriately.
        """
        path = proxy_adapter_test.path + 'node_{}'.format(proxy_adapter_test.num_targets-1)

        proxy_adapter_test.clear_access_counts()
        response = proxy_adapter_test.adapter.get(path, proxy_adapter_test.request)
        access_counts = [server.get_access_count() for server in proxy_adapter_test.test_servers]

        assert path in response.data
        assert sum(access_counts) == 1
