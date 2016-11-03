import sys
import json

from nose.tools import *

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock
else:                         # pragma: no cover
    from mock import Mock

from odin.http.routes.api import ApiRoute, ApiHandler, ApiError, _api_version
from odin.config.parser import AdapterConfig

class TestApiRoute():

    @classmethod
    def setup_class(cls):
        cls.api_route = ApiRoute()

    def test_api_route_has_handlers(self):
        assert (len(self.api_route.get_handlers()) > 0)

    def test_register_adapter(self):

        adapter_config = AdapterConfig('dummy', 'odin.adapters.dummy.DummyAdapter')
        self.api_route.register_adapter(adapter_config)

    def test_register_adapter_badmodule(self):

        adapter_config = AdapterConfig('dummy', 'odin.adapters.bad_dummy.DummyAdapter')

        with assert_raises_regexp(ApiError, 'No module named'):
            self.api_route.register_adapter(adapter_config, fail_ok=False)

    def test_register_adapter_badclass(self):

        adapter_config = AdapterConfig('dummy', 'odin.adapters.dummy.BadAdapter')

        with assert_raises_regexp(ApiError, 'has no attribute \'BadAdapter\''):
            self.api_route.register_adapter(adapter_config, fail_ok=False)


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

        # Create mock Tornado application and request objects for ApiHandler initialisation
        cls.app = Mock()
        cls.app.ui_methods = {}
        cls.request = Mock()

        # Create mock responses for ApiHandler test cases
        cls.json_dict_response = Mock()
        cls.json_dict_response.status_code = 200
        cls.json_dict_response.content_type = 'application/json'
        cls.json_dict_response.data = {'response': 'is_json'}

        cls.json_str_response = Mock()
        cls.json_str_response.status_code = 200
        cls.json_str_response.content_type = 'application/json'
        cls.json_str_response.data = json.dumps(cls.json_dict_response.data)

        # Create a mock route and a default adapter for a subsystem
        cls.route = Mock()
        cls.subsystem = 'default'
        cls.route.adapters = {}
        cls.route.adapter = lambda subsystem: cls.route.adapters[subsystem]
        cls.route.has_adapter = lambda subsystem: subsystem in cls.route.adapters

        cls.route.adapters[cls.subsystem] = Mock()
        cls.route.adapters[cls.subsystem].get.return_value = cls.json_dict_response
        cls.route.adapters[cls.subsystem].put.return_value = cls.json_dict_response
        cls.route.adapters[cls.subsystem].delete.return_value = cls.json_dict_response

        # Create the handler and mock its write method with the local version
        cls.handler = ApiHandler(cls.app, cls.request, route=cls.route)
        cls.handler.write = cls.mock_write

        cls.path = 'default/path'

    def test_handler_valid_get(self):

        self.handler.get(str(_api_version), self.subsystem, self.path)
        assert_equal(self.handler.get_status(), 200)
        assert_equal(json.loads(self.write_data), self.json_dict_response.data)

    def test_handler_valid_put(self):

        self.handler.put(str(_api_version), self.subsystem, self.path)
        assert_equal(self.handler.get_status(), 200)
        assert_equal(json.loads(self.write_data), self.json_dict_response.data)

    def test_handler_valid_delete(self):

        self.handler.delete(str(_api_version), self.subsystem, self.path)
        assert_equal(self.handler.get_status(), 200)
        assert_equal(json.loads(self.write_data), self.json_dict_response.data)

    def test_bad_api_version(self):

        bad_version = 0.1234
        self.handler.get(str(bad_version), self.subsystem, self.path)
        assert_equal(self.handler.get_status(), 400)
        assert_equal(self.write_data, "API version {} is not supported".format(bad_version))

    def test_bad_subsystem(self):

        bad_subsystem = 'missing'
        self.handler.get(str(_api_version), bad_subsystem, self.path)
        assert_equal(self.handler.get_status(), 400)
        assert_equal(self.write_data, "No API adapter registered for subsystem {}".format(bad_subsystem))

    def test_handler_response_json_str(self):

        self.handler.respond(self.json_str_response)
        assert_equal(self.write_data, self.json_str_response.data)

    def test_handler_response_json_dict(self):

        self.handler.respond(self.json_dict_response)
        assert_equal(self.write_data, self.json_str_response.data)

    def test_handler_response_json_bad_type(self):

        bad_response = Mock()
        bad_response.status_code = 200
        bad_response.content_type = 'application/json'
        bad_response.data = 1234

        with assert_raises_regexp(ApiError,
              'A response with content type application/json must have str or dict data'):
            self.handler.respond(bad_response)




