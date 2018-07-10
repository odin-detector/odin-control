import sys

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock, patch
else:                         # pragma: no cover
    from mock import Mock, patch

from nose.tools import *

import threading

from tornado.testing import AsyncHTTPTestCase, bind_unused_port
from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler
from tornado.httpserver import HTTPServer
import tornado.gen

from odin.adapters.proxy import ProxyTarget, ProxyAdapter

class ProxyTestHandler(RequestHandler):

    data = {'one': 1, 'two': 2.0, 'pi': 3.14}

    def get(self):
        self.write(ProxyTestHandler.data)

class TestProxyTarget():

    @classmethod
    def setup_class(cls):

        cls.server_ioloop = IOLoop()

        @tornado.gen.coroutine
        def init_server():
            sock, cls.port = bind_unused_port()
            app = Application([('/', ProxyTestHandler)])
            cls.server = HTTPServer(app)
            cls.server.add_socket(sock)
        cls.server_ioloop.run_sync(init_server)

        cls.server_thread = threading.Thread(target=cls.server_ioloop.start)
        cls.server_thread.start()
       
        cls.name = 'test_target'
        cls.url = 'http://127.0.0.1:{}/'.format(cls.port)
        cls.request_timeout = 0.1

        cls.proxy_target = ProxyTarget(cls.name, cls.url, cls.request_timeout)

    @classmethod
    def teardown_class(cls):

        cls.proxy_target.http_client.close()

        def stop_server():

            cls.server.stop()
            # Delay the shutdown of the IOLoop by several iterations because
            # the server may still have some cleanup work left when
            # the client finishes with the response (this is noticeable
            # with http/2, which leaves a Future with an unexamined
            # StreamClosedError on the loop).

            @tornado.gen.coroutine
            def slow_stop():
                # The number of iterations is difficult to predict. Typically,
                # one is sufficient, although sometimes it needs more.
                for i in range(5):
                    yield
                cls.server_ioloop.stop()
            cls.server_ioloop.add_callback(slow_stop)
        cls.server_ioloop.add_callback(stop_server)
        cls.server_thread.join()
        cls.server_ioloop.close(all_fds=True)

    def test_proxy_target_init(self):

        assert_equal(self.proxy_target.name, self.name)
        assert_equal(self.proxy_target.url, self.url)
        assert_equal(self.proxy_target.request_timeout, self.request_timeout)

    def test_proxy_target_update(self):

        self.proxy_target.last_update = ''

        self.proxy_target._update()
        assert_equal(self.proxy_target.data, TestHandler.data)
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

        cls.adapter_kwargs = {
            'targets': "node_1=http://127.0.0.1:8888/api/0.1/system_info/,"+
            "node_2=http://127.0.0.1:8887/api/0.1/system_info/",
            'request_timeout': 2.0,
        }
        cls.adapter = ProxyAdapter(**cls.adapter_kwargs)
        cls.path = ''
        cls.request = Mock
        cls.request.headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    @classmethod
    def teardown_class(cls):

        for target in cls.adapter.targets:
            target.http_client.close()

    def test_adapter_get(self):

        response = self.adapter.get(self.path, self.request)
        print(response.data)