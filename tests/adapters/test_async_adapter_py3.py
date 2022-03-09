import sys

import pytest

if sys.version_info[0] < 3:
    pytest.skip("Skipping async tests", allow_module_level=True)
else:
    from odin.adapters.async_adapter import AsyncApiAdapter
    from unittest.mock import Mock

class AsyncApiAdapterTestFixture(object):

    def __init__(self):
        self.adapter_options = {
            'test_option_float' : 1.234,
            'test_option_str' : 'value',
            'test_option_int' : 4567.
        }
        self.adapter = AsyncApiAdapter(**self.adapter_options)
        self.path = '/api/async_path'
        self.request = Mock()
        self.request.headers = {'Accept': '*/*', 'Content-Type': 'text/plain'}

@pytest.fixture(scope="class")
def test_async_api_adapter():
    test_async_api_adapter = AsyncApiAdapterTestFixture()
    yield test_async_api_adapter

class TestAsyncApiAdapter():
    """Class to test the AsyncApiAdapter object."""

    @pytest.mark.asyncio
    async def test_async_adapter_get(self, test_async_api_adapter):
        """
        Test the the adapter responds to a GET request correctly by returning a 400 code and
        appropriate message. This is due to the base adapter not implementing the methods.
        """
        response = await test_async_api_adapter.adapter.get(
            test_async_api_adapter.path, test_async_api_adapter.request)
        assert response.data == 'GET method not implemented by AsyncApiAdapter'
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_async_adapter_post(self, test_async_api_adapter):
        """
        Test the the adapter responds to a POST request correctly by returning a 400 code and
        appropriate message. This is due to the base adapter not implementing the methods.
        """
        response = await test_async_api_adapter.adapter.post(
            test_async_api_adapter.path, test_async_api_adapter.request)
        assert response.data == 'POST method not implemented by AsyncApiAdapter'
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_async_adapter_put(self, test_async_api_adapter):
        """
        Test the the adapter responds to a PUT request correctly by returning a 400 code and
        appropriate message. This is due to the base adapter not implementing the methods.
        """
        response = await test_async_api_adapter.adapter.put(
            test_async_api_adapter.path, test_async_api_adapter.request)
        assert response.data == 'PUT method not implemented by AsyncApiAdapter'
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_adapter_delete(self, test_async_api_adapter):
        """
        Test the the adapter responds to a DELETE request correctly by returning a 400 code and
        appropriate message. This is due to the base adapter not implementing the methods.
        """
        response = await test_async_api_adapter.adapter.delete(
            test_async_api_adapter.path, test_async_api_adapter.request)
        assert response.data == 'DELETE method not implemented by AsyncApiAdapter'
        assert response.status_code == 400
