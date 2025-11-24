import json

from tests.handlers.fixtures import test_api_adapter_info_handler

class TestApiAdapterInfoHandler():
    """Test cases for the ApiAdapterListHandler class."""

    def test_handler_initializes_route(self, test_api_adapter_info_handler):

        assert test_api_adapter_info_handler.handler.route == test_api_adapter_info_handler.route

    def test_api_adapter_info_handler_get_adapters(self, test_api_adapter_info_handler):

        test_api_adapter_info_handler.handler.get(test_api_adapter_info_handler.route.api_version)

        adapter_list = json.loads(test_api_adapter_info_handler.write_data)
        print(adapter_list)
        assert 'adapters' in adapter_list
        assert isinstance(adapter_list['adapters'], dict)
        assert test_api_adapter_info_handler.subsystem in adapter_list['adapters']

    def test_api_adapter_info_handler_invalid_version(self, test_api_adapter_info_handler):

        invalid_version = "9.9.9"
        test_api_adapter_info_handler.handler.get(invalid_version)

        assert test_api_adapter_info_handler.handler.get_status() == 400
        assert "is not supported" in test_api_adapter_info_handler.write_data

    def test_api_adapter_info_handler_invalid_accept(self, test_api_adapter_info_handler):

        test_api_adapter_info_handler.request.headers = {'Accept': 'text/plain'}
        test_api_adapter_info_handler.handler.get(test_api_adapter_info_handler.route.api_version)

        assert test_api_adapter_info_handler.handler.get_status() == 406
        assert "Request content types not supported" in test_api_adapter_info_handler.write_data
