import sys
import json

import pytest

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock
else:                         # pragma: no cover
    from mock import Mock

from odin.http.routes.api import ApiRoute, ApiHandler, ApiError, API_VERSION
from odin.config.parser import AdapterConfig


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