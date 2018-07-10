import sys
import threading
import logging

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock, patch
else:                         # pragma: no cover
    from mock import Mock, patch

from nose.tools import *

from tornado.testing import AsyncHTTPTestCase, bind_unused_port
from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler
from tornado.httpserver import HTTPServer
import tornado.gen

from odin.adapters.proxy import ProxyTarget, ProxyAdapter
from odin.testing.utils import LogCaptureFilter

class ProxyTestHandler(RequestHandler):

    data = {'one': 1, 'two': 2.0, 'pi': 3.14}

    def get(self):
        self.write(ProxyTestHandler.data)

class ProxyTestServer(object):

    def __init__(self):

        self.server_ioloop = IOLoop()

        @tornado.gen.coroutine
        def init_server():
            sock, self.port = bind_unused_port()
            app = Application([('/', ProxyTestHandler)])
            self.server = HTTPServer(app)
            self.server.add_socket(sock)
        self.server_ioloop.run_sync(init_server)

        self.server_thread = threading.Thread(target=self.server_ioloop.start)

    def start(self):

        self.server_thread.start()

    def stop(self):

        def stop_server():

            self.server.stop()

            @tornado.gen.coroutine
            def slow_stop():
                for i in range(5):
                    yield
                self.server_ioloop.stop()
            
            self.server_ioloop.add_callback(slow_stop)

        self.server_ioloop.add_callback(stop_server)
        self.server_thread.join()
        self.server_ioloop.close(all_fds=True)


class TestProxyTarget():

    @classmethod
    def setup_class(cls):

        cls.test_server = ProxyTestServer()
        cls.test_server.start()
        cls.port = cls.test_server.port

        cls.name = 'test_target'
        cls.url = 'http://127.0.0.1:{}/'.format(cls.port)
        cls.request_timeout = 0.1

        cls.proxy_target = ProxyTarget(cls.name, cls.url, cls.request_timeout)

    @classmethod
    def teardown_class(cls):

        cls.proxy_target.http_client.close()
        cls.test_server.stop()

    def test_proxy_target_init(self):

        assert_equal(self.proxy_target.name, self.name)
        assert_equal(self.proxy_target.url, self.url)
        assert_equal(self.proxy_target.request_timeout, self.request_timeout)

    def test_proxy_target_update(self):

        self.proxy_target.last_update = ''

        self.proxy_target._update()
        assert_equal(self.proxy_target.data, ProxyTestHandler.data)
        assert_equal(self.proxy_target.status_code, 200)
        assert_not_equal(self.proxy_target.last_update, '')

    def test_param_tree_get(self):

        param_tree = self.proxy_target.param_tree.get('')
        for tree_element in ['url', 'status_code', 'error', 'last_update']:
            assert_true(tree_element in param_tree)

    def test_proxy_target_http_error_404(self):

        bad_url = self.url + 'notfound'
        proxy_target = ProxyTarget(self.name, bad_url, self.request_timeout)
        proxy_target._update()
        
        assert_equal(proxy_target.status_code, 404)
        assert_in('Not Found', proxy_target.error_string)

    def test_proxy_target_other_error(self):

        bad_url = 'http://127.0.0.1:{}'.format(self.port + 1)
        proxy_target = ProxyTarget(self.name, bad_url, self.request_timeout)
        proxy_target._update()

        assert_equal(proxy_target.status_code, 502)
        assert_in('Connection refused', proxy_target.error_string)


class TestProxyAdapter():

    @classmethod
    def setup_class(cls):

        cls.log_capture_filter = LogCaptureFilter()
        logging.getLogger().setLevel(logging.DEBUG)

        cls.num_targets = 2

        cls.test_servers = []
        cls.ports = []
        cls.target_config = ""

        for _ in range(cls.num_targets):

            test_server = ProxyTestServer()
            test_server.start()
            cls.test_servers.append(test_server)
            cls.ports.append(test_server.port)

        cls.target_config = ','.join([
            "node_{}=http://127.0.0.1:{}/".format(tgt, port) for (tgt, port) in enumerate(cls.ports)
        ])

        cls.adapter_kwargs = {
            'targets': cls.target_config,
            'request_timeout': 1.0,
        }
        cls.adapter = ProxyAdapter(**cls.adapter_kwargs)

        cls.path = ''
        cls.request = Mock
        cls.request.headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    @classmethod
    def teardown_class(cls):

        for target in cls.adapter.targets:
            target.http_client.close()
        for test_server in cls.test_servers:
            test_server.stop()

    def test_adapter_loaded(self):

        expected_msg = "ProxyAdapter with {} targets loaded".format(self.num_targets)
        assert_true(expected_msg in self.log_capture_filter.log_debug())

    def test_adapter_get(self):

        response = self.adapter.get(self.path, self.request)
        
        assert_equal(len(response.data), self.num_targets)
        
        for tgt in range(self.num_targets):
            node_str = 'node_{}'.format(tgt)
            assert_true(node_str in response.data)
            assert_equal(response.data[node_str]['data'], ProxyTestHandler.data)

    def test_adapter_get_bad_path(self):

        missing_path = 'missing/path'
        response = self.adapter.get(missing_path, self.request)

        assert_true('error' in response.data)
        assert_equal('The path {} is invalid'.format(missing_path), response.data['error'])

    def test_adapter_bad_timeout(self):

        bad_timeout = 'not_timeout'
        bad_adapter = ProxyAdapter(request_timeout=bad_timeout)

        expected_msg = 'Illegal timeout specified for ProxyAdapter: {}'.format(bad_timeout)
        assert_true(expected_msg in self.log_capture_filter.log_error())

    def test_adapter_bad_target_spec(self):

        bad_target_spec = 'bad_target_1,bad_target_2'
        bad_adapter = ProxyAdapter(targets=bad_target_spec)

        expected_msg = 'Illegal target specification for ProxyAdapter: bad_target_1'
        assert_true(expected_msg in self.log_capture_filter.log_error())

    def test_adapter_no_target_spec(self):

        bad_adapter = ProxyAdapter()

        expected_msg = "Failed to resolve targets for ProxyAdapter"
        assert_true(expected_msg in self.log_capture_filter.log_error())
