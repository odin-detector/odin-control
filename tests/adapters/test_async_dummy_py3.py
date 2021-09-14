import sys

import pytest

if sys.version_info[0] < 3:
    pytest.skip("Skipping async tests", allow_module_level=True)
else:
    from odin.adapters.async_dummy import AsyncDummyAdapter
    from unittest.mock import Mock


class AsyncDummyAdapterTestFixture(object):
    """Container class used in fixtures for testing the AsyncDummyAdapter."""
    def __init__(self, wrap_sync_sleep=False):
        """
        Initialise the adapter and associated test objects.

        The wrap_sync_sleep argument steers the adapter options, controlling how
        the simulated task is executed, either wrapping a synchronous function
        or using native asyncio sleep.
        """

        self.adapter_options = {
            'wrap_sync_sleep': wrap_sync_sleep,
            'async_sleep_duration': 0.1
        }
        self.adapter = AsyncDummyAdapter(**self.adapter_options)
        self.path = '/dummy/path'
        self.request = Mock()
        self.request.body = '{}'
        self.request.headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

@pytest.fixture(scope='class', params=[True, False], ids=['wrapped', 'native'])
def test_dummy_adapter(request):
    """
    Parameterised test fixture for use with AsyncDummyAdapter tests. The fixture
    parameters generate tests using this fixture for both wrapped and native async task
    simulation.
    """
    test_dummy_adapter = AsyncDummyAdapterTestFixture(request.param)
    yield test_dummy_adapter


class TestDummyAdapterWrapped():

    @pytest.mark.asyncio
    async def test_adapter_get(self, test_dummy_adapter):

        expected_response = {
            'response': 'AsyncDummyAdapter: GET on path {}'.format(test_dummy_adapter.path)
        }
        response = await test_dummy_adapter.adapter.get(
            test_dummy_adapter.path, test_dummy_adapter.request)
        assert response.data == expected_response
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_adapter_put(self, test_dummy_adapter):

        expected_response = {
            'response': 'AsyncDummyAdapter: PUT on path {}'.format(test_dummy_adapter.path)
        }
        response = await test_dummy_adapter.adapter.put(
            test_dummy_adapter.path, test_dummy_adapter.request)
        assert response.data == expected_response
        assert response.status_code == 200
