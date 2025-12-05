import json

import pytest

from unittest.mock import Mock

from odin_control.http.handlers.api import ApiHandler, validate_api_request
from odin_control.http.handlers.api_adapter_info import ApiAdapterInfoHandler
from odin_control.http.handlers.api_version import ApiVersionHandler
from odin_control.adapters.adapter import ApiAdapterResponse
from odin_control.adapters.util import wrap_result

TEST_API_VERSION = "0.1"

class TestHandler(object):
    """Class to create appropriate mocked objects to allow the ApiHandler to be tested."""

    def __init__(self, handler_cls, async_adapter=True, api_version=None, **handler_kwargs):
        """Initialise the TestHandler."""
        self.handler_kwargs = handler_kwargs

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
        self.path = 'default/path'
        self.route.adapters = {}
        self.route.adapter = lambda subsystem: self.route.adapters[subsystem]
        self.route.has_adapter = lambda subsystem: subsystem in self.route.adapters
        self.route.api_version = api_version
        handler_kwargs['route'] = self.route

        # Create a mock API adapter that returns appropriate responses
        api_adapter_mock = Mock()
        api_adapter_mock.is_async = async_adapter
        api_adapter_mock.version = TEST_API_VERSION
        api_adapter_mock.__class__.__module__ = self.__class__.__module__
        api_adapter_mock.__class__.__name__ = 'TestApiAdapter'
        api_adapter_mock.get.return_value = wrap_result(self.json_dict_response, async_adapter)
        api_adapter_mock.post.return_value = wrap_result(self.json_dict_response, async_adapter)
        api_adapter_mock.put.return_value = wrap_result(self.json_dict_response, async_adapter)
        api_adapter_mock.delete.return_value = wrap_result(self.json_dict_response, async_adapter)
        self.route.adapters[self.subsystem] = api_adapter_mock

        # Create the handler and mock its write method with the local version
        self.handler = handler_cls(self.app, self.request, **handler_kwargs)

        self.handler.write = self.mock_write
        self.handler.dummy_get = self.dummy_get

        # self.respond = self.handler.respond
        self.headers = lambda: self.handler._headers

    def mock_write(self, chunk):
        """Mock write function to be used with the handler."""
        if isinstance(chunk, dict):
            self.write_data = json.dumps(chunk)
        else:
            self.write_data = chunk

    @validate_api_request
    def dummy_get(self, subsystem, path=''):
        """Dummy HTTP GET verb method to allow the request validation decorator to be tested."""
        response = ApiAdapterResponse(
            {'subsystem': subsystem, 'path': path },
            content_type='application/json',
            status_code=200
        )
        self.respond(response)

@pytest.fixture(scope="class", params=[True, False], ids=["async", "sync"])
def test_api_handler(request):
    """Parameterised test fixture for testing the ApiHandler class sync/async support."""
    test_api_handler = TestHandler(
        ApiHandler, async_adapter=request.param, api_version=TEST_API_VERSION,
        enable_cors=False, cors_origin="*"
    )
    yield test_api_handler

@pytest.fixture(scope="class")
def test_api_handler_no_versioning():
    """Test fixture for testing the ApiHandler class with no API versioning."""
    test_api_handler_no_versioning = TestHandler(
        ApiHandler, async_adapter=False, api_version=None, enable_cors=False, cors_origin="*"
    )
    yield test_api_handler_no_versioning

@pytest.fixture(scope="class", params=[True, False], ids=["CORS enabled", "CORS disabled"])
def test_api_handler_cors(request):
    """Parameterised test fixture for testing the ApiHandler class CORS support."""
    test_api_handler_cors = TestHandler(
        ApiHandler, async_adapter=False, enable_cors=request.param, cors_origin="*"
    )
    yield test_api_handler_cors

@pytest.fixture(scope="class", params=[None, TEST_API_VERSION], ids=["no versioning", "versioned"])
def test_api_adapter_info_handler(request):
    """Parameterised test fixture for testing the ApiAdapterInfoHandler class."""
    test_api_adapter_info_handler = TestHandler(
        ApiAdapterInfoHandler, async_adapter=False, api_version=request.param
    )
    test_api_adapter_info_handler.request.headers = {'Accept': 'application/json'}
    yield test_api_adapter_info_handler

@pytest.fixture(scope="class", params=[None, TEST_API_VERSION], ids=["no versioning", "versioned"])
def test_api_version_handler(request):
    """Test fixture for testing the ApiVersionHandler class."""
    test_api_version_handler = TestHandler(
        ApiVersionHandler, async_adapter=False, api_version=request.param
    )
    test_api_version_handler.request.headers = {'Accept': 'application/json'}
    yield test_api_version_handler
