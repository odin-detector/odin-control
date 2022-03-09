import sys
import json

import pytest

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock
else:                         # pragma: no cover
    from mock import Mock


from odin.http.handlers.base import BaseApiHandler, API_VERSION, ApiError, validate_api_request
from odin.adapters.adapter import ApiAdapterResponse
from tests.handlers.fixtures import test_base_handler


class TestBaseApiHandler(object):
    """Test cases for the BaseApiHandler class."""

    def test_handler_initializes_route(self, test_base_handler):
        """
        Check that the handler route has been set, i.e that that handler has its
        initialize method called.
        """
        assert test_base_handler.handler.route == test_base_handler.route

    def test_handler_response_json_str(self, test_base_handler):
        """Test that the handler respond correctly deals with a string response."""
        test_base_handler.handler.respond(test_base_handler.json_str_response)
        assert test_base_handler.write_data == test_base_handler.json_str_response.data

    def test_handler_response_json_dict(self, test_base_handler):
        """Test that the handler respond correctly deals with a dict response."""
        test_base_handler.handler.respond(test_base_handler.json_dict_response)
        assert test_base_handler.write_data ==  test_base_handler.json_str_response.data

    def test_handler_respond_valid_json(self, test_base_handler):
        """Test that the base handler respond method handles a valid JSON ApiAdapterResponse."""
        data = {'valid': 'json', 'value': 1.234}
        valid_response = ApiAdapterResponse(data, content_type="application/json")
        test_base_handler.handler.respond(valid_response)
        assert test_base_handler.handler.get_status() == 200
        assert json.loads(test_base_handler.write_data) == data

    def test_handler_respond_invalid_json(self, test_base_handler):
        """
        Test that the base handler respond method raises an ApiError when passed
        an invalid response.
        """
        invalid_response = ApiAdapterResponse(1234, content_type="application/json")
        with pytest.raises(ApiError) as excinfo:
            test_base_handler.handler.respond(invalid_response)

        assert 'A response with content type application/json must have str or dict data' \
            in str(excinfo.value)

    def test_handler_get(self, test_base_handler):
        """Test that the base handler get method raises a not implemented error."""
        with pytest.raises(NotImplementedError):
            test_base_handler.handler.get(
                test_base_handler.subsystem, test_base_handler.path)

    def test_handler_post(self, test_base_handler):
        """Test that the base handler post method raises a not implemented error."""
        with pytest.raises(NotImplementedError):
            test_base_handler.handler.post(
                test_base_handler.subsystem, test_base_handler.path)

    def test_handler_put(self, test_base_handler):
        """Test that the base handler put method raises a not implemented error."""
        with pytest.raises(NotImplementedError):
            test_base_handler.handler.put(
                test_base_handler.subsystem, test_base_handler.path)

    def test_handler_delete(self, test_base_handler):
        """Test that the base handler delete method raises a not implemented error."""
        with pytest.raises(NotImplementedError):
            test_base_handler.handler.delete(
                test_base_handler.subsystem, test_base_handler.path)


class TestHandlerRequestValidation():
    """Test cases for the validate_api_request decorator."""

    def test_invalid_api_request_version(self, test_base_handler):
        """
        Check that a request with an invalid API version is intercepted by the decorator
        and returns an appropriate HTTP response.
        """
        bad_version = 0.1234
        test_base_handler.handler.dummy_get(
            str(bad_version), test_base_handler.subsystem, test_base_handler.path
        )
        assert test_base_handler.handler.get_status() == 400
        assert "API version {} is not supported".format(bad_version) in test_base_handler.write_data

    def test_invalid_subsystem_request(self, test_base_handler):
        """
        Check that a request with an invalid subsystem, i.e. one which does not have an
        adapter registered, is intercepted by the decorator and returns an appropriate
        HTTP response.
        """
        bad_subsystem = 'bad_subsys'
        test_base_handler.handler.dummy_get(
            str(API_VERSION), bad_subsystem, test_base_handler.path
        )
        assert test_base_handler.handler.get_status() == 400
        assert "No API adapter registered for subsystem {}".format(bad_subsystem) \
            in test_base_handler.write_data

    def test_valid_request(self, test_base_handler):
        """
        Check that a request with a valid API version and subsystem is not intercepted by
        the decorator and calls the verb method correctly.
        """
        test_base_handler.handler.dummy_get(
            str(API_VERSION), test_base_handler.subsystem, test_base_handler.path
        )
        assert test_base_handler.handler.get_status() == 200




