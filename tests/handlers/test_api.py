import json

import pytest

from odin_control.http.handlers.api import API_VERSION, ApiError
from odin_control.adapters.adapter import ApiAdapterResponse
from tests.handlers.fixtures import test_api_handler, test_api_handler_cors

class TestApiHandler():
    """Test cases for the ApiHandler class."""

    @pytest.mark.asyncio
    async def test_handler_initializes_route(self, test_api_handler):
        """
        Test that the handler route has been set, i.e that that handler has its
        initialize method called.
        """
        assert test_api_handler.handler.route == test_api_handler.route

    def test_handler_response_json_str(self, test_api_handler):
        """Test that the handler respond correctly deals with a string response."""
        test_api_handler.handler.respond(test_api_handler.json_str_response)
        assert test_api_handler.write_data == test_api_handler.json_str_response.data

    def test_handler_response_json_dict(self, test_api_handler):
        """Test that the handler respond correctly deals with a dict response."""
        test_api_handler.handler.respond(test_api_handler.json_dict_response)
        assert test_api_handler.write_data ==  test_api_handler.json_str_response.data

    def test_handler_respond_valid_json(self, test_api_handler):
        """Test that the base handler respond method handles a valid JSON ApiAdapterResponse."""
        data = {'valid': 'json', 'value': 1.234}
        valid_response = ApiAdapterResponse(data, content_type="application/json")
        test_api_handler.handler.respond(valid_response)
        assert test_api_handler.handler.get_status() == 200
        assert json.loads(test_api_handler.write_data) == data

    def test_handler_respond_invalid_json(self, test_api_handler):
        """
        Test that the base handler respond method raises an ApiError when passed
        an invalid response.
        """
        invalid_response = ApiAdapterResponse(1234, content_type="application/json")
        with pytest.raises(ApiError) as excinfo:
            test_api_handler.handler.respond(invalid_response)

        assert 'A response with content type application/json must have str or dict data' \
            in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_handler_valid_get(self, test_api_handler):
        """Test that the handler creates a valid status and response to a GET request."""
        await test_api_handler.handler.get(str(API_VERSION),
            test_api_handler.subsystem, test_api_handler.path)
        assert test_api_handler.handler.get_status() == 200
        assert json.loads(test_api_handler.write_data) == test_api_handler.json_dict_response.data

    @pytest.mark.asyncio
    async def test_handler_valid_post(self, test_api_handler):
        """Test that the handler creates a valid status and response to a POST request."""
        await test_api_handler.handler.post(str(API_VERSION),
            test_api_handler.subsystem, test_api_handler.path)
        assert test_api_handler.handler.get_status() == 200
        assert json.loads(test_api_handler.write_data) == test_api_handler.json_dict_response.data

    @pytest.mark.asyncio
    async def test_handler_valid_put(self, test_api_handler):
        """Test that the handler creates a valid status and response to a PUT request."""
        await test_api_handler.handler.put(str(API_VERSION),
            test_api_handler.subsystem, test_api_handler.path)
        assert test_api_handler.handler.get_status() == 200
        assert json.loads(test_api_handler.write_data) == test_api_handler.json_dict_response.data

    @pytest.mark.asyncio
    async def test_handler_valid_delete(self, test_api_handler):
        """Test that the handler creates a valid status and response to a DELETE request."""
        await test_api_handler.handler.delete(str(API_VERSION),
            test_api_handler.subsystem, test_api_handler.path)
        assert test_api_handler.handler.get_status() == 200
        assert json.loads(test_api_handler.write_data) == test_api_handler.json_dict_response.data

    @pytest.mark.asyncio
    async def test_bad_api_version(self, test_api_handler):
        """Test that a bad API version in a GET call to the handler yields an error."""
        bad_version = 0.1234
        await test_api_handler.handler.get(str(bad_version),
            test_api_handler.subsystem, test_api_handler.path)
        assert test_api_handler.handler.get_status() == 400
        assert "API version {} is not supported".format(bad_version) in test_api_handler.write_data

    @pytest.mark.asyncio
    async def test_bad_subsystem(self, test_api_handler):
        """Test that a bad subsystem in a GET call to the handler yields an error."""
        bad_subsystem = 'missing'
        await test_api_handler.handler.get(str(API_VERSION), bad_subsystem, test_api_handler.path)
        assert test_api_handler.handler.get_status() == 400
        assert "No API adapter registered for subsystem {}".format(bad_subsystem) \
            in test_api_handler.write_data

class TestApiHandlerCorsSupport():

    def test_cors_headers(self, test_api_handler_cors):
        test_api_handler_cors.handler.options(
            test_api_handler_cors.subsystem, test_api_handler_cors.path)
        cors_headers = [
            "Access-Control-Allow-Origin",
            "Access-Control-Allow-Headers",
            "Access-Control-Allow-Methods"
        ]

        headers = test_api_handler_cors.headers()
        for cors_header in cors_headers:
            if test_api_handler_cors.handler_kwargs.get('enable_cors', False):
                assert cors_header in headers
            else:
                assert cors_header not in headers