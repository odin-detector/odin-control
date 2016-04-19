import sys
import json

import tornado.web

from nose.tools import *

if sys.version_info[0] == 3:
    from unittest.mock import Mock, patch
else:
    from mock import Mock, patch

from odin.http.routes.api import ApiRoute, ApiHandler, ApiError, _api_version


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

    @classmethod
    def mock_write(cls, chunk):
        if isinstance(chunk, dict):
            cls.write_data = json.dumps(chunk)
        else:
            cls.write_data = chunk

    @classmethod
    def setup_class(cls):

        # Initialise attribute to receive output of patched write() method
        cls.write_data = None

        # Patch the base class of ApiHandler, i.e. replace tornado.web.RequestHandler,
        # which allows testing to take place without the need to instantiate a full
        # tornado web application
        print(ApiHandler.__bases__)
        cls.patcher = patch.object(ApiHandler, '__bases__', (Mock,))
        cls.mock_request_handler = cls.patcher.start()
        print("PATCHER STARTED")
        print(ApiHandler.__bases__)

        cls.patcher.is_local = True

        # # Create the patched handler and mock its write method with the local version
        # cls.handler = ApiHandler()
        # cls.handler.write = cls.mock_write
        #
        # cls.json_dict_response = Mock()
        # cls.json_dict_response.status_code = 200
        # cls.json_dict_response.content_type = 'application/json'
        # cls.json_dict_response.data = {'response': 'is_json'}
        #
        # cls.json_str_response = Mock()
        # cls.json_str_response.status_code = 200
        # cls.json_str_response.content_type = 'application/json'
        # cls.json_str_response.data = json.dumps(cls.json_dict_response.data)
        #
        # # Create a mock route and a default adapter for a subsystem
        # cls.route = Mock()
        # cls.subsystem = 'default'
        # cls.route.adapters = {}
        # cls.route.adapter = lambda subsystem: cls.route.adapters[subsystem]
        #
        # cls.route.adapters[cls.subsystem] = Mock()
        # cls.route.adapters[cls.subsystem].get.return_value = cls.json_dict_response
        # cls.route.adapters[cls.subsystem].put.return_value = cls.json_dict_response
        # cls.route.adapters[cls.subsystem].delete.return_value = cls.json_dict_response
        # cls.handler.initialize(cls.route)

    @classmethod
    def teardown_class(cls):
        print("PATCHER STOPPED")
        print(ApiHandler.__bases__)

        cls.patcher.stop()
        print(ApiHandler.__bases__)
        cls.patcher = patch.object(ApiHandler, '__bases__', (tornado.web.RequestHandler))

        print(ApiHandler.__bases__)

    def test_nothing(self):

        assert_equal(1, 1)

    # def test_handler_valid_get(self):
    #
    #     path = '/handler/test'
    #
    #     self.handler.get(str(_api_version), self.subsystem, path)
    #     assert_equal(json.loads(self.write_data), self.json_dict_response.data)
    #
    # def test_handler_response_json_str(self):
    #
    #     self.handler.respond(self.json_str_response)
    #     assert_equal(self.write_data, self.json_str_response.data)
    #
    # def test_handler_response_json_dict(self):
    #
    #     self.handler.respond(self.json_dict_response)
    #     assert_equal(self.write_data, self.json_str_response.data)
    #
    # def test_handler_response_json_bad_type(self):
    #
    #     bad_response = Mock()
    #     bad_response.status_code = 200
    #     bad_response.content_type = 'application/json'
    #     bad_response.data = 1234
    #
    #     with assert_raises_regexp(ApiError,
    #           'A response with content type application/json must have str or dict data'):
    #         self.handler.respond(bad_response)




