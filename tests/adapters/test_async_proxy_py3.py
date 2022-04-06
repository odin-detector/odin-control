"""
Unit tests for the odin-control AsyncProxyAdapter class.

Tim Nicholls, STFC Detector Systems Software Group.
"""

import logging
import sys
from io import StringIO

import pytest
from zmq import proxy

if sys.version_info[0] < 3:
    pytest.skip("Skipping async tests", allow_module_level=True)
else:
    import asyncio
    from tornado.ioloop import TimeoutError
    from tornado.httpclient import HTTPResponse
    from odin.adapters.async_proxy import AsyncProxyTarget, AsyncProxyAdapter
    from unittest.mock import Mock
    from tests.adapters.test_proxy import ProxyTestHandler, ProxyTargetTestFixture, ProxyTestServer
    from odin.util import convert_unicode_to_string
    from tests.utils import log_message_seen
    from tests.async_utils import AwaitableTestFixture, asyncio_fixture_decorator
    try:
        from unittest.mock import AsyncMock
    except ImportError:
        from tests.async_utils import AsyncMock


@pytest.fixture
def test_proxy_target():
    test_proxy_target = ProxyTargetTestFixture(AsyncProxyTarget)
    yield test_proxy_target
    test_proxy_target.stop()


class TestAsyncProxyTarget():
    """Test cases for the AsyncProxyTarget class."""

    @pytest.mark.asyncio
    async def test_async_proxy_target_init(self, test_proxy_target):
        """Test the proxy target is correctly initialised."""
        assert test_proxy_target.proxy_target.name == test_proxy_target.name
        assert test_proxy_target.proxy_target.url == test_proxy_target.url
        assert test_proxy_target.proxy_target.request_timeout == test_proxy_target.request_timeout

    @pytest.mark.asyncio
    async def test_async_proxy_target_remote_get(self, test_proxy_target):
        """Test the that remote GET to a proxy target succeeds."""
        test_proxy_target.proxy_target.last_update = ''

        await test_proxy_target.proxy_target.remote_get()
        assert test_proxy_target.proxy_target.data == ProxyTestHandler.param_tree.get("")
        assert test_proxy_target.proxy_target.status_code == 200
        assert test_proxy_target.proxy_target.last_update != ''

    def test_async_proxy_target_param_tree_get(self, test_proxy_target):
        """Test that a proxy target get returns a parameter tree."""
        param_tree = test_proxy_target.proxy_target.status_param_tree.get('')
        for tree_element in ['url', 'status_code', 'error', 'last_update']:
            assert tree_element in param_tree

    @pytest.mark.asyncio
    async def test_async_proxy_target_http_get_error_404(self, test_proxy_target):
        """Test that a proxy target GET to a bad URL returns a 404 not found error."""
        bad_url = test_proxy_target.url + 'notfound/'
        proxy_target = await AsyncProxyTarget(
            test_proxy_target.name, bad_url, test_proxy_target.request_timeout
        )
        await proxy_target.remote_get('notfound')

        assert proxy_target.status_code == 404
        assert 'Not Found' in proxy_target.error_string

    @pytest.mark.asyncio
    async def test_async_proxy_target_timeout_error(self, test_proxy_target):
        """Test that a proxy target GET request that times out is handled correctly"""
        mock_fetch = Mock()
        mock_fetch.side_effect = TimeoutError('timeout')
        proxy_target = await AsyncProxyTarget(
            test_proxy_target.name, test_proxy_target.url, test_proxy_target.request_timeout
        )
        proxy_target.http_client.fetch = mock_fetch

        await proxy_target.remote_get()

        assert proxy_target.status_code == 408
        assert 'timeout' in proxy_target.error_string

    @pytest.mark.asyncio
    async def test_async_proxy_target_io_error(self, test_proxy_target):
        """Test that a proxy target GET request to a non-existing server returns a 502 error."""
        bad_url = 'http://127.0.0.1:{}'.format(test_proxy_target.port + 1)
        proxy_target = await AsyncProxyTarget(
            test_proxy_target.name, bad_url, test_proxy_target.request_timeout
        )
        await proxy_target.remote_get()

        assert proxy_target.status_code == 502
        assert 'Connection refused' in proxy_target.error_string

    @pytest.mark.asyncio
    async def test_async_proxy_target_unknown_error(self, test_proxy_target):
        """Test that a proxy target GET request handles an unknown exception returning a 500 error."""
        mock_fetch = Mock()
        mock_fetch.side_effect = ValueError('value error')
        proxy_target = await AsyncProxyTarget(
            test_proxy_target.name, test_proxy_target.url, test_proxy_target.request_timeout
        )
        proxy_target.http_client.fetch = mock_fetch

        await proxy_target.remote_get()

        assert proxy_target.status_code == 500
        assert 'value error' in proxy_target.error_string

    @pytest.mark.asyncio
    async def test_async_proxy_target_traps_decode_error(self, test_proxy_target):
        """Test that a proxy target correctly traps errors decoding a non-JSON response body."""
        mock_fetch = AsyncMock()
        mock_fetch.return_value = HTTPResponse(Mock(), 200, buffer=StringIO(u"wibble"))

        proxy_target = await AsyncProxyTarget(
            test_proxy_target.name, test_proxy_target.url, test_proxy_target.request_timeout
        )
        proxy_target.http_client.fetch = mock_fetch

        await proxy_target.remote_get()

        assert proxy_target.status_code == 415
        assert "Failed to decode response body" in proxy_target.error_string


class AsyncProxyAdapterTestFixture(AwaitableTestFixture):
    """Container class used in fixtures for testing async proxy adapters."""

    def __init__(self):

        super(AsyncProxyAdapterTestFixture, self).__init__(AsyncProxyAdapter)

        """Initialise the fixture, setting up the AsyncProxyAdapter with the correct configuration."""
        self.num_targets = 2

        self.test_servers = []
        self.ports = []
        self.target_config = ""

        # Launch the appropriate number of target test servers.""""
        for _ in range(self.num_targets):

            test_server = ProxyTestServer()
            self.test_servers.append(test_server)
            self.ports.append(test_server.port)

        self.target_config = ','.join([
            "node_{}=http://127.0.0.1:{}/".format(tgt, port) for (tgt, port) in enumerate(self.ports)
        ])

        self.adapter_kwargs = {
            'targets': self.target_config,
            'request_timeout': 1.0,
        }
        self.adapter = AsyncProxyAdapter(**self.adapter_kwargs)

        self.path = ''
        self.request = Mock()
        self.request.headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        self.request.body = '{"pi":2.56}'

    def __del__(self):
        """Ensure the test servers are stopped on deletion."""
        self.stop()

    def stop(self):
        """Stop the proxied test servers, ensuring any client connections to them are closed."""
        for target in self.adapter.targets:
            target.http_client.close()
        for test_server in self.test_servers:
            test_server.stop()

    def clear_access_counts(self):
        """Clear the access counters in all test servers."""
        for test_server in self.test_servers:
            test_server.clear_access_count()

@pytest.fixture(scope="class")
def event_loop():
    """Redefine the pytest.asyncio event loop fixture to have class scope."""
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

@asyncio_fixture_decorator(scope='class')
async def async_proxy_adapter_test():
    async_proxy_adapter_test = await AsyncProxyAdapterTestFixture()
    adapters = [async_proxy_adapter_test]
    await async_proxy_adapter_test.adapter.initialize([adapters])
    yield async_proxy_adapter_test
    await async_proxy_adapter_test.adapter.cleanup()

class TestAsyncProxyAdapter():

    def test_adapter_loaded(self, async_proxy_adapter_test):
        assert len(async_proxy_adapter_test.adapter.targets) == async_proxy_adapter_test.num_targets

    @pytest.mark.asyncio
    async def test_adapter_get(self, async_proxy_adapter_test):
        """
        Test that a GET request to the proxy adapter returns the appropriate data for all
        defined proxied targets.
        """
        response = await async_proxy_adapter_test.adapter.get(
            async_proxy_adapter_test.path, async_proxy_adapter_test.request)

        assert 'status' in response.data

        assert len(response.data) == async_proxy_adapter_test.num_targets + 1

        for tgt in range(async_proxy_adapter_test.num_targets):
            node_str = 'node_{}'.format(tgt)
            assert node_str in response.data
            assert response.data[node_str], ProxyTestHandler.data

    @pytest.mark.asyncio
    async def test_adapter_get_metadata(self, async_proxy_adapter_test):
        request = async_proxy_adapter_test.request
        request.headers['Accept'] = "{};{}".format(request.headers['Accept'], "metadata=True")
        response = await async_proxy_adapter_test.adapter.get(async_proxy_adapter_test.path, request)

        assert "status" in response.data
        for target in range(async_proxy_adapter_test.num_targets):
            node_str = 'node_{}'.format(target)
            assert node_str in response.data
            assert "one" in response.data[node_str]
            assert "type" in response.data[node_str]['one']

    @pytest.mark.asyncio
    async def test_adapter_get_status_metadata(self, async_proxy_adapter_test):
        request = async_proxy_adapter_test.request
        request.headers['Accept'] = "{};{}".format(request.headers['Accept'], "metadata=True")
        response = await async_proxy_adapter_test.adapter.get(async_proxy_adapter_test.path, request)

        assert 'status' in response.data
        assert 'node_0' in response.data['status']
        assert 'type' in response.data['status']['node_0']['error']

    @pytest.mark.asyncio
    async def test_adapter_put(self, async_proxy_adapter_test):
        """
        Test that a PUT request to the proxy adapter returns the appropriate data for all
        defined proxied targets.
        """
        response = await async_proxy_adapter_test.adapter.put(
            async_proxy_adapter_test.path, async_proxy_adapter_test.request)

        assert 'status' in response.data

        assert len(response.data) == async_proxy_adapter_test.num_targets + 1

        for tgt in range(async_proxy_adapter_test.num_targets):
            node_str = 'node_{}'.format(tgt)
            assert node_str in response.data
            assert convert_unicode_to_string(response.data[node_str]) == ProxyTestHandler.param_tree.get("")

    @pytest.mark.asyncio
    async def test_adapter_get_proxy_path(self, async_proxy_adapter_test):
        """Test that a GET to a sub-path within a targer succeeds and return the correct data."""
        node = async_proxy_adapter_test.adapter.targets[0].name
        path = "more/even_more"
        response = await async_proxy_adapter_test.adapter.get(
            "{}/{}".format(node, path), async_proxy_adapter_test.request)

        assert response.data["even_more"] == ProxyTestHandler.data["more"]["even_more"]
        assert async_proxy_adapter_test.adapter.param_tree.get('')['status'][node]['status_code'] == 200

    @pytest.mark.asyncio
    async def test_adapter_get_proxy_path_trailing_slash(self, async_proxy_adapter_test):
        """
        Test that a PUT to a sub-path with a trailing slash in the URL within a targer succeeds
        and returns the correct data.
        """
        node = async_proxy_adapter_test.adapter.targets[0].name
        path = "more/even_more/"
        response = await async_proxy_adapter_test.adapter.get(
            "{}/{}".format(node, path), async_proxy_adapter_test.request)

        assert response.data["even_more"] == ProxyTestHandler.data["more"]["even_more"]
        assert async_proxy_adapter_test.adapter.param_tree.get('')['status'][node]['status_code'] == 200

    @pytest.mark.asyncio
    async def test_adapter_put_proxy_path(self, async_proxy_adapter_test):
        """
        Test that a PUT to a sub-path without a trailing slash in the URL within a targer succeeds
        and returns the correct data.
        """
        node = async_proxy_adapter_test.adapter.targets[0].name
        path = "more"
        async_proxy_adapter_test.request.body = '{"replace": "been replaced"}'
        response = await async_proxy_adapter_test.adapter.put(
            "{}/{}".format(node, path), async_proxy_adapter_test.request)

        assert async_proxy_adapter_test.adapter.param_tree.get('')['status'][node]['status_code'] == 200
        assert convert_unicode_to_string(response.data["more"]["replace"]) == "been replaced"

    @pytest.mark.asyncio
    async def test_adapter_get_bad_path(self, async_proxy_adapter_test):
        """Test that a GET to a bad path within a target returns the appropriate error."""
        missing_path = 'missing/path'
        response = await async_proxy_adapter_test.adapter.get(missing_path, async_proxy_adapter_test.request)

        assert 'error' in response.data
        assert 'Invalid path: {}'.format(missing_path) == response.data['error']

    @pytest.mark.asyncio
    async def test_adapter_put_bad_path(self, async_proxy_adapter_test):
        """Test that a PUT to a bad path within a target returns the appropriate error."""
        missing_path = 'missing/path'
        response = await async_proxy_adapter_test.adapter.put(missing_path, async_proxy_adapter_test.request)

        assert 'error' in response.data
        assert 'Invalid path: {}'.format(missing_path) == response.data['error']

    @pytest.mark.asyncio
    async def test_adapter_put_bad_type(self, async_proxy_adapter_test):
        """Test that a PUT request with an inappropriate type returns the appropriate error."""
        async_proxy_adapter_test.request.body = "bad_body"
        response = await async_proxy_adapter_test.adapter.put(
            async_proxy_adapter_test.path, async_proxy_adapter_test.request)

        assert 'error' in response.data
        assert 'Failed to decode PUT request body:' in response.data['error']

    @pytest.mark.asyncio
    async def test_adapter_bad_timeout(self, async_proxy_adapter_test, caplog):
        """Test that a bad timeout specified for the proxy adatper yields a logged error message."""
        bad_timeout = 'not_timeout'
        _ = await AsyncProxyAdapter(request_timeout=bad_timeout)

        assert log_message_seen(caplog, logging.ERROR,
            'Illegal timeout specified for proxy adapter: {}'.format(bad_timeout))

    @pytest.mark.asyncio
    async def test_adapter_bad_target_spec(self, caplog):
        """
        Test that an incorrectly formatted target specified passed to a proxy adapter yields a
        logged error message.
        """
        bad_target_spec = 'bad_target_1,bad_target_2'
        _ = await AsyncProxyAdapter(targets=bad_target_spec)

        assert log_message_seen(caplog, logging.ERROR,
            "Illegal target specification for proxy adapter: bad_target_1")

    @pytest.mark.asyncio
    async def test_adapter_no_target_spec(self, caplog):
        """
        Test that a proxy adapter instantiated with no target specifier yields a logged
        error message.
        """
        _ = await AsyncProxyAdapter()

        assert log_message_seen(caplog, logging.ERROR,
            "Failed to resolve targets for proxy adapter")

    @pytest.mark.asyncio
    async def test_adapter_get_access_count(self, async_proxy_adapter_test):
        """
        Test that requests via the proxy adapter correctly increment the access counters in the
        target test servers.
        """
        async_proxy_adapter_test.clear_access_counts()

        _ = await async_proxy_adapter_test.adapter.get(
            async_proxy_adapter_test.path, async_proxy_adapter_test.request
        )

        access_counts = [server.get_access_count() for server in async_proxy_adapter_test.test_servers]
        assert access_counts == [1]*async_proxy_adapter_test.num_targets

    @pytest.mark.asyncio
    async def test_adapter_counter_get_single_node(self, async_proxy_adapter_test):
        """
        Test that a requested to a single target in the proxy adapter only accesses that target,
        increasing the access count appropriately.
        """
        path = async_proxy_adapter_test.path + 'node_{}'.format(async_proxy_adapter_test.num_targets-1)

        async_proxy_adapter_test.clear_access_counts()
        response = await async_proxy_adapter_test.adapter.get(path, async_proxy_adapter_test.request)
        access_counts = [server.get_access_count() for server in async_proxy_adapter_test.test_servers]

        assert path in response.data
        assert sum(access_counts) == 1
