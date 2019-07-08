""" Unit tests for the ODIN ProxyAdapter.

Tim Nicholls, STFC Application Engineering Group.
"""

import sys
import threading
import logging

import pytest

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock, patch
else:                         # pragma: no cover
    from mock import Mock, patch

from tornado.testing import AsyncHTTPTestCase, bind_unused_port
from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler
from tornado.httpserver import HTTPServer
import tornado.gen

from odin.adapters.proxy import ProxyTarget, ProxyAdapter
from odin.testing.utils import LogCaptureFilter, log_message_seen

class ProxyTestHandler(RequestHandler):
    """ Tornado request handler for use in test server needed for proxy tests."""

    # Data structure served by request handler
    data = {'one': 1,
            'two': 2.0,
            'pi': 3.14,
            'more':
            {
                'three': 3.0,
                'replace': 'Replace Me!',
                'even_more':{
                    'extra_val': 5.5
                }
            }
        }

    def initialize(self, server):
        """Increment the server access count every time the request handler is invoked."""
        server.access_count += 1

    def get(self, path=''):
        """Handle GET requests to the test 0server."""
        try:
            data_ref = self.data
            if path:
                path_elems = path.split('/')
                for elem in path_elems[:-1]:
                    data_ref = data_ref[elem]
                self.write(data_ref)
            else:
                self.write(ProxyTestHandler.data)                
        except KeyError:
            self.set_status(404)
            self.write_error(404)
        except Exception as other_e:
            logging.error("ProxyTestHandler GET failed:", str(other_e))
            self.write_error(500)
    
    def put(self, path):
        """Handle PUT requests to the test server."""
        response_body = response_body = tornado.escape.json_decode(self.request.body)
        try:
            data_ref = self.data
            if path:
                path_elems = path.split('/')
                for elem in path_elems[:-1]:
                    data_ref = data_ref[elem]
                for key in response_body:
                    new_elem = response_body[key]
                    data_ref[key] = new_elem
                self.write(data_ref)
            else:
                self.write(ProxyTestHandler.data)
        except KeyError:
            self.set_status(404)
            self.write_error(404)        
        except Exception as other_e:
            logging.error("ProxyTestHandler PUT failed:", str(other_e))
            self.write_error(500)

                
class ProxyTestServer(object):
    """ Tornado test server for use in proxy testing."""
    def __init__(self,):
        """Initialise the server."""
        self.server_ioloop = IOLoop()
        self.access_count = 0

        @tornado.gen.coroutine
        def init_server():
            """Initiliase the server, running in a co-routine."""
            sock, self.port = bind_unused_port()
            app = Application([('/(.*)', ProxyTestHandler, dict(server=self))])
            self.server = HTTPServer(app)
            self.server.add_socket(sock)
        self.server_ioloop.run_sync(init_server)

        self.server_thread = threading.Thread(target=self.server_ioloop.start)

    def start(self):
        """Start the server thread."""
        self.server_thread.start()

    def stop(self):
        """Stop the server, using a lazy callback added to the server IOLoop."""
        def stop_server():

            self.server.stop()

            @tornado.gen.coroutine
            def slow_stop():
                for _ in range(5):
                    yield
                self.server_ioloop.stop()
            
            self.server_ioloop.add_callback(slow_stop)

        self.server_ioloop.add_callback(stop_server)
        self.server_thread.join()
        self.server_ioloop.close(all_fds=True)

    def get_access_count(self):
        """Return the server access count."""
        return self.access_count

    def clear_access_count(self):
        """Clear the server access count."""
        self.access_count = 0


class ProxyTargetTestFixture(object):
    """Container class used in fixtures for testing ProxyTarget."""
    def __init__(self):
        """Initialise the fixture, starting the test server and defining a target."""
        self.test_server = ProxyTestServer()
        self.test_server.start()
        self.port = self.test_server.port

        self.name = 'test_target'
        self.url = 'http://127.0.0.1:{}/'.format(self.port)
        self.request_timeout = 0.1

        self.proxy_target = ProxyTarget(self.name, self.url, self.request_timeout)

    def __del__(self):
        """Ensure test server is stopped on deletion."""
        self.stop()

    def stop(self):
        """Stop the test server and proxy HTTP client."""
        self.proxy_target.http_client.close()
        self.test_server.stop()       


@pytest.fixture(scope="class")
def test_proxy_target():
    """Fixture used in ProxyTarget test cases."""
    test_proxy_target = ProxyTargetTestFixture()
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
        assert test_proxy_target.proxy_target.data == ProxyTestHandler.data
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

    def test_proxy_target_other_error(self, test_proxy_target):
        """Test that a proxy target GET request to a non-existing server returns a 502 error."""
        bad_url = 'http://127.0.0.1:{}'.format(test_proxy_target.port + 1)
        proxy_target = ProxyTarget(test_proxy_target.name, bad_url,
            test_proxy_target.request_timeout)
        proxy_target.remote_get()

        assert proxy_target.status_code == 502
        assert 'Connection refused' in proxy_target.error_string


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
            test_server.start()
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
        self.request = Mock
        self.request.headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        self.request.body = '{"pi":2.56}'

    def __del__(self):
        """Ensure the test servers are stopped on deletion."""
        self.stop()

    def stop(self):
        """Stop the proxied test servers, ensuring any client connections to them are closed."""
        for target in self.adapter.targets: 
            target.http_client.close()
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

class TestProxyAdapter():
    """Test cases for testing the ProxyAdapter class."""

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
        
        assert len(response.data) ==  proxy_adapter_test.num_targets+1
        
        for tgt in range(proxy_adapter_test.num_targets):
            node_str = 'node_{}'.format(tgt)
            assert node_str in response.data
            assert response.data[node_str], ProxyTestHandler.data
    
    def test_adapter_put(self, proxy_adapter_test):
        """
        Test that a PUT request to the proxy adapter returns the appropriate data for all
        defined proxied targets.
        """
        response = proxy_adapter_test.adapter.put(
            proxy_adapter_test.path, proxy_adapter_test.request)

        assert 'status' in response.data

        assert len(response.data) == proxy_adapter_test.num_targets+1

        for tgt in range(proxy_adapter_test.num_targets):
            node_str = 'node_{}'.format(tgt)
            assert node_str in response.data
            assert response.data[node_str] == ProxyTestHandler.data

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
        Test that a PUT to a sub-path withouta trailing slash in the URL within a targer succeeds 
        and returns the correct data.
        """
        node = proxy_adapter_test.adapter.targets[0].name
        path = "more/replace"
        proxy_adapter_test.request.body = '{"replace": "been replaced"}'
        response = proxy_adapter_test.adapter.put(
            "{}/{}".format(node, path), proxy_adapter_test.request)

        assert proxy_adapter_test.adapter.param_tree.get('')['status'][node]['status_code'] == 200
        assert response.data["replace"] == "been replaced"

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
            'Illegal timeout specified for ProxyAdapter: {}'.format(bad_timeout))

    def test_adapter_bad_target_spec(self, proxy_adapter_test, caplog):
        """
        Test that an incorrectly formatted target specified passed to a proxy adapter yields a
        logged error message.
        """
        bad_target_spec = 'bad_target_1,bad_target_2'
        _ = ProxyAdapter(targets=bad_target_spec)

        assert log_message_seen(caplog, logging.ERROR, 
            "Illegal target specification for ProxyAdapter: bad_target_1")

    def test_adapter_no_target_spec(self, caplog):
        """
        Test that a proxy adapter instantiated with no target specifier yields a logged 
        error message.
        """
        _ = ProxyAdapter()

        assert log_message_seen(caplog, logging.ERROR, 
            "Failed to resolve targets for ProxyAdapter")

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
