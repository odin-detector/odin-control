import sys

import pytest

if sys.version_info[0] < 3:
    pytest.skip("Skipping async tests", allow_module_level=True)
else:
    try:
        from unittest.mock import AsyncMock
    except ImportError:
        from tests.utils_async_py3 import AsyncMock


from odin.http.routes.api import ApiRoute
from odin.config.parser import AdapterConfig

class ApiRouteAsyncTestFixture(object):

    def __init__(self):

        self.route = ApiRoute()
        self.adapter_name = 'async_dummy'
        self.adapter_module = 'odin.adapters.async_dummy.AsyncDummyAdapter'
        self.adapter_config = AdapterConfig(self.adapter_name, self.adapter_module)

        self.route.register_adapter(self.adapter_config)
        
        self.initialize_mock = AsyncMock()
        self.route.adapters[self.adapter_name].initialize = self.initialize_mock

        self.cleanup_mock = AsyncMock()
        self.route.adapters[self.adapter_name].cleanup = self.cleanup_mock

@pytest.fixture(scope="class")
def test_api_route_async():
    """Test fixture used in testing ApiRoute behaviour with async adapters"""

    test_api_route_async = ApiRouteAsyncTestFixture()
    yield test_api_route_async


class TestApiRouteAsync(object):

    def test_register_async_adapter(self, test_api_route_async):

        assert test_api_route_async.route.has_adapter('async_dummy')

    def test_initialize_async_adapter(self, test_api_route_async):

        test_api_route_async.route.initialize_adapters()
        test_api_route_async.initialize_mock.assert_awaited_once()

    def test_cleanup_async_adapter(self, test_api_route_async):

        test_api_route_async.route.cleanup_adapters()
        test_api_route_async.cleanup_mock.assert_awaited_once()