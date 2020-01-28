import sys
import json

import pytest

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock
else:                         # pragma: no cover
    from mock import Mock

from odin.http.routes.api import ApiRoute, ApiHandler, ApiError, API_VERSION
from odin.config.parser import AdapterConfig

@pytest.fixture(scope="class")
def test_api_route():
    """Simple test fixture that creates an ApiRoute object."""
    ar = ApiRoute()
    yield ar

class TestApiRoute(object):
    """Class to test the behaviour of the ApiRoute."""

    def test_api_route_has_handlers(self, test_api_route):
        """Test that the default ApiRoute object has handlers."""
        assert len(test_api_route.get_handlers()) > 0

    def test_register_adapter(self, test_api_route):
        """Test that it is possible to register an adapter with the API route object."""
        adapter_config = AdapterConfig('dummy', 'odin.adapters.dummy.DummyAdapter')
        test_api_route.register_adapter(adapter_config)

        assert test_api_route.has_adapter('dummy')

    def test_register_adapter_badmodule(self, test_api_route):
        """Test that registering an adapter with a bad module name raises an error."""
        adapter_name = 'dummy'
        adapter_config = AdapterConfig(adapter_name, 'odin.adapters.bad_dummy.DummyAdapter')

        with pytest.raises(ApiError) as excinfo:
            test_api_route.register_adapter(adapter_config, fail_ok=False)

            assert 'No module named {}'.format(adapter_name) in str(excinfo.value)

    def test_register_adapter_badclass(self, test_api_route):
        """Test that registering an adapter with a bad class name raises an error."""
        adapter_config = AdapterConfig('dummy', 'odin.adapters.dummy.BadAdapter')

        with pytest.raises(ApiError) as excinfo:
            test_api_route.register_adapter(adapter_config, fail_ok=False)

        assert 'has no attribute \'BadAdapter\'' in str(excinfo.value)

    def test_register_adapter_no_cleanup(self, test_api_route):
        """
        Test that attempting to clean up an adapter without a cleanup method doesn't 
        cause an error
        """
        adapter_name = 'dummy_no_clean'
        adapter_config = AdapterConfig(adapter_name, 'odin.adapters.dummy.DummyAdapter')
        test_api_route.register_adapter(adapter_config)
        test_api_route.adapters[adapter_name].cleanup = Mock(side_effect=AttributeError())

        raised = False
        try:
            test_api_route.cleanup_adapters()
        except:
            raised = True

        assert not raised

    def test_register_adapter_no_initialize(self, test_api_route):
        """
        Test that attempting to inialize an adapter without an initialize method doesn't
        raise an error.
        """
        adapter_name = 'dummy_no_clean'
        adapter_config = AdapterConfig(adapter_name, 'odin.adapters.dummy.DummyAdapter')
        test_api_route.register_adapter(adapter_config)
        test_api_route.adapters[adapter_name].initialize = Mock(side_effect=AttributeError())

        raised = False
        try:
            test_api_route.initialize_adapters()
        except:
            raised = True

        assert not raised

class ApiTestHandler(object):
    """Class to create appropriate mocked objects to allow the ApiHandler to be tested."""

    def __init__(self):
        """Initialise the ApiTestHandler."""
        # Initialise attribute to receive output of patched write() method
        self.write_data = None

        # Create mock Tornado application and request objects for ApiHandler initialisation
        self.app = Mock()
        self.app.ui_methods = {}
        self.request = Mock()

        # Create mock responses for ApiHandler test cases
        self.json_dict_response = Mock()
        self.json_dict_response.status_code = 200
        self.json_dict_response.content_type = 'application/json'
        self.json_dict_response.data = {'response': 'is_json'}

        self.json_str_response = Mock()
        self.json_str_response.status_code = 200
        self.json_str_response.content_type = 'application/json'
        self.json_str_response.data = json.dumps(self.json_dict_response.data)

        # Create a mock route and a default adapter for a subsystem
        self.route = Mock()
        self.subsystem = 'default'
        self.route.adapters = {}
        self.route.adapter = lambda subsystem: self.route.adapters[subsystem]
        self.route.has_adapter = lambda subsystem: subsystem in self.route.adapters

        self.route.adapters[self.subsystem] = Mock()
        self.route.adapters[self.subsystem].get.return_value = self.json_dict_response
        self.route.adapters[self.subsystem].put.return_value = self.json_dict_response
        self.route.adapters[self.subsystem].delete.return_value = self.json_dict_response

        # Create the handler and mock its write method with the local version
        self.handler = ApiHandler(self.app, self.request, route=self.route)
        self.handler.write = self.mock_write

        self.path = 'default/path'

    def mock_write(self, chunk):
        """Mock write function to be used with the handler."""
        if isinstance(chunk, dict):
            self.write_data = json.dumps(chunk)
        else:
            self.write_data = chunk
            
@pytest.fixture(scope="class")
def test_api_handler():
    """Simple test fixture that creates a test API handler.""" 
    test_api_handler = ApiTestHandler()
    yield test_api_handler

class TestApiHandler(object):

    def test_handler_valid_get(self, test_api_handler):
        """Test that the handler creates a valid status and response to a GET request."""
        test_api_handler.handler.get(str(API_VERSION),
            test_api_handler.subsystem, test_api_handler.path)
        assert test_api_handler.handler.get_status() == 200
        assert json.loads(test_api_handler.write_data) == test_api_handler.json_dict_response.data

    def test_handler_valid_put(self, test_api_handler):
        """Test that the handler creates a valid status and response to a PUT request."""
        test_api_handler.handler.put(str(API_VERSION),
            test_api_handler.subsystem, test_api_handler.path)
        assert test_api_handler.handler.get_status() == 200
        assert json.loads(test_api_handler.write_data) == test_api_handler.json_dict_response.data

    def test_handler_valid_delete(self, test_api_handler):
        """Test that the handler creates a valid status and response to a PUT request."""
        test_api_handler.handler.delete(str(API_VERSION),
            test_api_handler.subsystem, test_api_handler.path)
        assert test_api_handler.handler.get_status() == 200
        assert json.loads(test_api_handler.write_data) == test_api_handler.json_dict_response.data

    def test_bad_api_version(self, test_api_handler):
        """Test that a bad API version in a GET call to the handler yields an error."""
        bad_version = 0.1234
        test_api_handler.handler.get(str(bad_version), 
            test_api_handler.subsystem, test_api_handler.path)
        assert test_api_handler.handler.get_status() == 400
        assert "API version {} is not supported".format(bad_version) in test_api_handler.write_data

    def test_bad_subsystem(self, test_api_handler):
        """Test that a bad subsystem in a GET call to the handler yields an error."""
        bad_subsystem = 'missing'
        test_api_handler.handler.get(str(API_VERSION), bad_subsystem, test_api_handler.path)
        assert test_api_handler.handler.get_status() == 400
        assert "No API adapter registered for subsystem {}".format(bad_subsystem) \
            in test_api_handler.write_data

    def test_handler_response_json_str(self, test_api_handler):
        """Test that the handler respond correctly deals with a string response."""
        test_api_handler.handler.respond(test_api_handler.json_str_response)
        assert test_api_handler.write_data == test_api_handler.json_str_response.data

    def test_handler_response_json_dict(self, test_api_handler):
        """Test that the handler respond correctly deals with a dict response."""
        test_api_handler.handler.respond(test_api_handler.json_dict_response)
        assert test_api_handler.write_data ==  test_api_handler.json_str_response.data

    def test_handler_response_json_bad_type(self, test_api_handler):
        """Test that the handler raises an error if an incorrect type of response is returned."""
        bad_response = Mock()
        bad_response.status_code = 200
        bad_response.content_type = 'application/json'
        bad_response.data = 1234

        with pytest.raises(ApiError) as excinfo:
            test_api_handler.handler.respond(bad_response)
        
        assert 'A response with content type application/json must have str or dict data' \
            in str(excinfo.value)
