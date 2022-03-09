import sys
import json

import pytest

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock
else:                         # pragma: no cover
    from mock import Mock

from odin.http.routes.api import ApiRoute, ApiHandler, ApiError, API_VERSION
from odin.config.parser import AdapterConfig
from tests.handlers.fixtures import test_api_handler

class TestApiHandler(object):

    def test_handler_valid_get(self, test_api_handler):
        """Test that the handler creates a valid status and response to a GET request."""
        test_api_handler.handler.get(str(API_VERSION),
            test_api_handler.subsystem, test_api_handler.path)
        assert test_api_handler.handler.get_status() == 200
        assert json.loads(test_api_handler.write_data) == test_api_handler.json_dict_response.data

    def test_handler_valid_post(self, test_api_handler):
        """Test that the handler creates a valid status and response to a POST request."""
        test_api_handler.handler.post(str(API_VERSION),
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
