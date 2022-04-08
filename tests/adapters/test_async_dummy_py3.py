import sys

import pytest

if sys.version_info[0] < 3:
    pytest.skip("Skipping async tests", allow_module_level=True)
else:
    import asyncio
    from odin.adapters.async_dummy import AsyncDummyAdapter
    from unittest.mock import Mock
    from tests.async_utils import AwaitableTestFixture, asyncio_fixture_decorator


class AsyncDummyAdapterTestFixture(AwaitableTestFixture):
    """Container class used in fixtures for testing the AsyncDummyAdapter."""
    def __init__(self, wrap_sync_sleep=False):
        """
        Initialise the adapter and associated test objects.

        The wrap_sync_sleep argument steers the adapter options, controlling how
        the simulated task is executed, either wrapping a synchronous function
        or using native asyncio sleep.
        """

        super(AsyncDummyAdapterTestFixture, self).__init__(AsyncDummyAdapter)

        self.adapter_options = {
            'wrap_sync_sleep': wrap_sync_sleep,
            'async_sleep_duration': 0.1
        }
        self.adapter = AsyncDummyAdapter(**self.adapter_options)
        self.path = ''
        self.bad_path = 'missing/path'
        self.rw_path = 'async_rw_param'
        self.request = Mock()
        self.request.body = '{}'
        self.request.headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

@pytest.fixture(scope="class")
def event_loop():
    """Redefine the pytest.asyncio event loop fixture to have class scope."""
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

@asyncio_fixture_decorator(scope='class', params=[True, False], ids=['wrapped', 'native'])
async def test_dummy_adapter(request):
    """
    Parameterised test fixture for use with AsyncDummyAdapter tests. The fixture
    parameters generate tests using this fixture for both wrapped and native async task
    simulation.
    """
    test_dummy_adapter = await AsyncDummyAdapterTestFixture(request.param)
    adapters = [test_dummy_adapter.adapter]
    await test_dummy_adapter.adapter.initialize(adapters)
    yield test_dummy_adapter
    await test_dummy_adapter.adapter.cleanup()


@pytest.mark.asyncio
class TestAsyncDummyAdapter():

    async def test_adapter_get(self, test_dummy_adapter):

        response = await test_dummy_adapter.adapter.get(
            test_dummy_adapter.path, test_dummy_adapter.request)
        assert isinstance(response.data, dict)
        assert response.status_code == 200

    async def test_adapter_get_bad_path(self, test_dummy_adapter):

        expected_response = {'error': 'Invalid path: {}'.format(test_dummy_adapter.bad_path)}
        response = await test_dummy_adapter.adapter.get(
            test_dummy_adapter.bad_path, test_dummy_adapter.request)
        assert response.data == expected_response
        assert response.status_code == 400

    async def test_adapter_put(self, test_dummy_adapter):

        rw_request = Mock()
        rw_request.headers = test_dummy_adapter.request.headers
        rw_request.body = 4567

        await test_dummy_adapter.adapter.put(test_dummy_adapter.rw_path, rw_request)

        response = await test_dummy_adapter.adapter.get(
            test_dummy_adapter.rw_path, test_dummy_adapter.request)

        assert isinstance(response.data, dict)
        assert response.data[test_dummy_adapter.rw_path] == rw_request.body
        assert response.status_code == 200

    async def test_adapter_put_bad_path(self, test_dummy_adapter):

        expected_response = {'error': 'Invalid path: {}'.format(test_dummy_adapter.bad_path)}
        response = await test_dummy_adapter.adapter.put(
            test_dummy_adapter.bad_path, test_dummy_adapter.request
        )
        assert response.data == expected_response
        assert response.status_code == 400