import sys
import json

import pytest

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock
    import asyncio
    async_allowed = True
else:                         # pragma: no cover
    from mock import Mock
    async_allowed = False

from odin.http.handlers.base import BaseApiHandler, API_VERSION, ApiError, validate_api_request
from odin.http.routes.api import ApiHandler
from odin.adapters.adapter import ApiAdapterResponse
from odin.config.parser import AdapterConfig
from odin.util import wrap_result


class TestHandler(object):
    """Class to create appropriate mocked objects to allow the ApiHandler to be tested."""

    def __init__(self, handler_cls, async_adapter=async_allowed, enable_cors=False):
        """Initialise the TestHandler."""
        self.enable_cors = enable_cors

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

        # Create a mock API adapter that returns appropriate responses
        api_adapter_mock = Mock()
        api_adapter_mock.is_async = async_adapter
        api_adapter_mock.get.return_value = wrap_result(self.json_dict_response, async_adapter)
        api_adapter_mock.post.return_value = wrap_result(self.json_dict_response, async_adapter)
        api_adapter_mock.put.return_value = wrap_result(self.json_dict_response, async_adapter)
        api_adapter_mock.delete.return_value = wrap_result(self.json_dict_response, async_adapter)
        self.route.adapters[self.subsystem] = api_adapter_mock

        # Create the handler and mock its write method with the local version
        self.handler = handler_cls(self.app, self.request,
            route=self.route, enable_cors=self.enable_cors, cors_origin="*"
        )
        self.handler.write = self.mock_write
        self.handler.dummy_get = self.dummy_get

        self.respond = self.handler.respond
        self.headers = lambda: self.handler._headers

    def mock_write(self, chunk):
        """Mock write function to be used with the handler."""
        if isinstance(chunk, dict):
            self.write_data = json.dumps(chunk)
        else:
            self.write_data = chunk

    @validate_api_request(API_VERSION)
    def dummy_get(self, subsystem, path=''):
        """Dummy HTTP GET verb method to allow the request validation decorator to be tested."""
        response = ApiAdapterResponse(
            {'subsystem': subsystem, 'path': path },
            content_type='application/json',
            status_code=200
        )
        self.respond(response)

if async_allowed:
    fixture_params = [True, False]
    fixture_ids = ["async", "sync"]
else:
    fixture_params = [False]
    fixture_ids = ["sync"]

@pytest.fixture(scope="class", params=fixture_params, ids=fixture_ids)
def test_api_handler(request):
    """
    Parameterised test fixture for testing the APIHandler class.

    The fixture parameters and id lists are set depending on whether async code is
    allowed on the current platform (e.g. python 2 vs 3).
    """
    test_api_handler = TestHandler(ApiHandler, async_adapter=request.param)
    yield test_api_handler

@pytest.fixture(scope="class")
def test_base_handler():
    """Test fixture for testing the BaseHandler class."""
    test_base_handler = TestHandler(BaseApiHandler)
    yield test_base_handler

@pytest.fixture(scope="class", params=[True, False], ids=["CORS enabled", "CORS disabled"])
def test_base_handler_cors(request):
    """Test fixture for testing the BaseHandler class."""
    test_base_handler = TestHandler(BaseApiHandler, enable_cors=request.param)
    yield test_base_handler
