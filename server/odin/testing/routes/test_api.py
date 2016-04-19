import sys

from nose.tools import *

if sys.version_info[0] == 3:
    from unittest.mock import Mock
else:
    from mock import Mock

from odin.http.routes.api import ApiRoute, ApiHandler, ApiError, _api_version

import tornado.web
import tornado.httputil

class TestApiRoute():

    @classmethod
    def setup_class(cls):
        cls.api_route = ApiRoute()

    def test_api_route_has_handlers(self):
        assert (len(self.api_route.get_handlers()) > 0)

    def test_register_adapter(self):

        self.api_route.register_adapter('dummy', 'odin.adapters.dummy.DummyAdapter')

    def test_register_adapter_badmodule(self):

        with assert_raises_regexp(ApiError, 'No module named'):
            self.api_route.register_adapter('dummy', 'odin.adapters.dummyd.DummyAdapter', fail_ok=False)

    def test_register_adapter_badclass(self):

        with assert_raises_regexp(ApiError, 'has no attribute \'BadAdapter\''):
            self.api_route.register_adapter('dummy', 'odin.adapters.dummy.BadAdapter', fail_ok=False)


class TestApiHandler():

    def test_handler_response_json(self):
        application = Mock()
        application.ui_methods = {}
        request = Mock()
        handler = ApiHandler(application, request, route=None)
        handler.write = Mock()

        response = Mock()
        response.status_code = 200
        response.content_type = 'application/json'
        response.data = '{\'response\' : \'is_json\'}'

        #handler.respond(response)

# class TestApiHandler():
#
#     @classmethod
#     def setup_class(cls):
#         cls.app = tornado.web.Application()
#         cls.request = tornado.httputil.HTTPServerRequest()
#         cls.api_route = ApiRoute()
#         cls.api_route.register_adapter('dummy', 'odin.adapters.dummy.DummyAdapter')
#         cls.api_handler = ApiHandler(cls.app, None)
#
#     def test_api_handler_get(self):
#
#         (data, code) = self.api_handler.get(_api_version, 'dummy', 'dummy_path')
#         print data, code

