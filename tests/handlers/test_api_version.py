import json

from tests.handlers.fixtures import test_api_version_handler

class TestApiVersionHandler():
    """Test cases for the ApiVersionHandler class."""

    def test_handler_valid_get(self, test_api_version_handler):
        """Test that the handler creates a valid status and response to a GET request."""
        test_api_version_handler.handler.get()
        assert test_api_version_handler.handler.get_status() == 200
        response_data = json.loads(test_api_version_handler.write_data)
        assert 'version' in response_data
        assert response_data['version'] == test_api_version_handler.route.api_version

    def test_handler_invalid_accept(self, test_api_version_handler):

        test_api_version_handler.request.headers = {'Accept': 'text/plain'}
        test_api_version_handler.handler.get()

        assert test_api_version_handler.handler.get_status() == 406
        assert "Requested content types not supported" in test_api_version_handler.write_data
