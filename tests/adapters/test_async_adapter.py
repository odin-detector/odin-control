from unittest.mock import AsyncMock, Mock

import pytest

from odin_control._version import __version__
from odin_control.adapters.async_adapter import AsyncApiAdapter
from odin_control.adapters.async_base_controller import AsyncBaseController, BaseError


class AsyncApiAdapterTestFixture(object):

    def __init__(self,adapter_cls):
        self.adapter_options = {
            'test_option_float' : 1.234,
            'test_option_str' : 'value',
            'test_option_int' : 4567.
        }
        self.adapter = adapter_cls(**self.adapter_options)
        self.path = '/api/async_path'
        self.request = Mock()
        self.request.headers = {'Accept': '*/*', 'Content-Type': 'application/json'}
        self.request.body = b'{}'

@pytest.fixture(scope="class")
def test_async_api_adapter():
    test_async_api_adapter = AsyncApiAdapterTestFixture(AsyncApiAdapter)
    yield test_async_api_adapter

class TestAsyncApiAdapter():
    """Class to test the AsyncApiAdapter object."""

    @pytest.mark.asyncio
    async def test_async_adapter_get(self, test_async_api_adapter):
        """Test that the adapter responds to a GET request correctly by returning a 405 code and
        appropriate message due to the lack of a controller.
        """
        response = await test_async_api_adapter.adapter.get(
            test_async_api_adapter.path, test_async_api_adapter.request)
        assert response.data == {'error': 'Adapter AsyncApiAdapter has no controller configured'}
        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_async_adapter_post(self, test_async_api_adapter):
        """Test that the adapter responds to a POST request correctly by returning a 405 code and
        appropriate message due to the lack of a controller.
        """
        response = await test_async_api_adapter.adapter.post(
            test_async_api_adapter.path, test_async_api_adapter.request)
        assert response.data == {'error': 'Adapter AsyncApiAdapter has no controller configured'}
        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_async_adapter_put(self, test_async_api_adapter):
        """Test that the adapter responds to a PUT request correctly by returning a 405 code and
        appropriate message due to the lack of a controller.
        """
        response = await test_async_api_adapter.adapter.put(
            test_async_api_adapter.path, test_async_api_adapter.request)
        assert response.data == {'error': 'Adapter AsyncApiAdapter has no controller configured'}
        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_adapter_delete(self, test_async_api_adapter):
        """Test that the adapter responds to a DELETE request correctly by returning a 405 code and
        appropriate message due to the lack of a controller.
        """
        response = await test_async_api_adapter.adapter.delete(
            test_async_api_adapter.path, test_async_api_adapter.request)
        assert response.data == {'error': 'Adapter AsyncApiAdapter has no controller configured'}
        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_adapter_initialize(self, test_async_api_adapter, caplog):
        """"Test that the initialize method logs the correct message when no controller is set."""
        with caplog.at_level('DEBUG'):
            await test_async_api_adapter.adapter.initialize({})
            assert any(record.levelname == 'WARNING' for record in caplog.records)
            assert f"{test_async_api_adapter.adapter.name} initialize called" in caplog.text
            assert f"{test_async_api_adapter.adapter.name} "
            "has no controller configured" in caplog.text

    @pytest.mark.asyncio
    async def test_adapter_cleanup(self, test_async_api_adapter, caplog):
        """Test that the cleanup function logs the correct message when no controller is set."""
        with caplog.at_level('DEBUG'):
            await test_async_api_adapter.adapter.cleanup()
            assert any(record.levelname == 'WARNING' for record in caplog.records)
            assert f"{test_async_api_adapter.adapter.name} cleanup called" in caplog.text
            assert f"{test_async_api_adapter.adapter.name} "
            "has no controller configured" in caplog.text

@pytest.fixture(scope="class")
def test_async_api_adapter_with_incomplete_controller():
    """Simple test fixture used for testing ApiAdapter with an incomplete controller."""
    test_async_api_adapter = AsyncApiAdapterTestFixture(AsyncApiAdapter)
    test_async_api_adapter.adapter.controller = AsyncMock()
    test_async_api_adapter.adapter.controller.initialize.side_effect = AttributeError
    test_async_api_adapter.adapter.controller.cleanup.side_effect = AttributeError
    test_async_api_adapter.adapter.controller.set.side_effect = NotImplementedError
    test_async_api_adapter.adapter.controller.create.side_effect = NotImplementedError
    test_async_api_adapter.adapter.controller.delete.side_effect = NotImplementedError

    yield test_async_api_adapter

class TestAsyncApiAdapterWithIncompleteController():
    """Class to test the ApiAdapter object with a controller."""

    @pytest.mark.asyncio
    async def test_adapter_with_controller_initialize(
        self, test_async_api_adapter_with_incomplete_controller, caplog
    ):
        """Test that an adapter with a controller catched a missing controller initialize method."""
        with caplog.at_level('DEBUG'):
            await test_async_api_adapter_with_incomplete_controller.adapter.initialize({})
            assert any(record.levelname == 'WARNING' for record in caplog.records)
            assert (f"{test_async_api_adapter_with_incomplete_controller.adapter.name} "
                   f"controller has no initialize method" in caplog.text)

    @pytest.mark.asyncio
    async def test_adapter_with_controller_cleanup(
            self, test_async_api_adapter_with_incomplete_controller, caplog
    ):
        """Test that an adapter with a controller catched a missing controller cleanup method."""
        with caplog.at_level('DEBUG'):
            await test_async_api_adapter_with_incomplete_controller.adapter.cleanup()
            assert any(record.levelname == 'WARNING' for record in caplog.records)
            assert (f"{test_async_api_adapter_with_incomplete_controller.adapter.name} "
                   f"controller has no cleanup method" in caplog.text)

    @pytest.mark.asyncio
    async def test_adapter_with_controller_get(
            self, test_async_api_adapter_with_incomplete_controller
        ):
        """Test that an adapter with a controller calls the controller get method."""
        await test_async_api_adapter_with_incomplete_controller.adapter.get(
            test_async_api_adapter_with_incomplete_controller.path,
            test_async_api_adapter_with_incomplete_controller.request
        )
        assert test_async_api_adapter_with_incomplete_controller.adapter.controller.get.called

    @pytest.mark.asyncio
    async def test_adapter_with_controller_put(
            self, test_async_api_adapter_with_incomplete_controller
        ):
        """Test that a PUT to an adapter with an incomplete controller (no set method) handles
        NotImplementedError.
        """
        response = await test_async_api_adapter_with_incomplete_controller.adapter.put(
            test_async_api_adapter_with_incomplete_controller.path,
            test_async_api_adapter_with_incomplete_controller.request
        )
        assert response.data == {
            "error": f"{test_async_api_adapter_with_incomplete_controller.adapter.name} "
                     "does not support PUT requests"
        }
        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_adapter_with_controller_post(
            self, test_async_api_adapter_with_incomplete_controller
        ):
        """Test that a POST to an adapter with an incomplete controller (no create method) handles
        NotImplementedError.
        """
        response = await test_async_api_adapter_with_incomplete_controller.adapter.post(
            test_async_api_adapter_with_incomplete_controller.path,
            test_async_api_adapter_with_incomplete_controller.request
        )
        assert response.data == {
            "error": f"{test_async_api_adapter_with_incomplete_controller.adapter.name} "
                     "does not support POST requests"
        }
        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_adapter_with_controller_delete(
            self, test_async_api_adapter_with_incomplete_controller
        ):
        """Test that a DELETE to an adapter with an incomplete controller (no delete method)
        handles NotImplementedError.
        """
        response = await test_async_api_adapter_with_incomplete_controller.adapter.delete(
            test_async_api_adapter_with_incomplete_controller.path,
            test_async_api_adapter_with_incomplete_controller.request
        )
        assert response.data == {
            "error": f"{test_async_api_adapter_with_incomplete_controller.adapter.name} "
                     "does not support DELETE requests"
        }
        assert response.status_code == 405

class AsyncApiAdapterTestController(AsyncBaseController):
    """Simple test controller for testing ApiAdapter with a controller."""
    def __init__(self, options):
        self.options = options

    async def get(self, path, with_metadata=False):
        """Mock get method."""
        if 'error' in path:
            raise BaseError("Test error raised from controller get method")

        return {"response": f"get called on path {path} with_metadata={with_metadata}"}

    async def set(self, path, data):
        """Mock set method."""
        if 'error' in path:
            raise BaseError("Test error raised from controller set method")

        return {"response": f"set called on path {path} with data={data}"}

    async def create(self, path, data):
        """Mock create method."""
        if 'error' in path:
            raise BaseError("Test error raised from controller create method")

        return data

    async def delete(self, path):
        """Mock delete method."""
        if 'error' in path:
            raise BaseError("Test error raised from controller delete method")

        return {"response": f"delete called on path {path}"}

class AsyncApiAdapterTestAdapter(AsyncApiAdapter):

    version = __version__
    controller_cls = AsyncApiAdapterTestController
    error_cls = BaseError

@pytest.fixture(scope="class")
def test_async_api_adapter_with_controller():
    """Simple test fixture used for testing ApiAdapter with a controller."""
    test_async_api_adapter = AsyncApiAdapterTestFixture(AsyncApiAdapterTestAdapter)
    yield test_async_api_adapter

class TestAsyncApiAdapterWithController():

    @pytest.mark.asyncio
    async def test_async_adapter_with_controller_init(self):
        """Test that an adapter with a controller is awaited correctly on initialization."""
        adapter = await AsyncApiAdapterTestAdapter(option1='value1', option2='value2')
        assert isinstance(adapter.controller, AsyncApiAdapterTestController)
        assert adapter.controller.options['option1'] == 'value1'
        assert adapter.controller.options['option2'] == 'value2'

    @pytest.mark.asyncio
    async def test_async_adapter_with_controller_initialize(
        self, test_async_api_adapter_with_controller, caplog
    ):
        """Test that an adapter with a controller calls the controller initialize method."""
        with caplog.at_level('DEBUG'):
            try:
                await test_async_api_adapter_with_controller.adapter.initialize({})
            except Exception as exc:
                pytest.fail(f"Adapter initialize raised an exception: {exc}")
            assert any(record.levelname == 'DEBUG' for record in caplog.records)
            assert (f"{test_async_api_adapter_with_controller.adapter.name} initialize called" in
                    caplog.text)

    @pytest.mark.asyncio
    async def test_async_adapter_with_controller_cleanup(
        self, test_async_api_adapter_with_controller, caplog
    ):
        """Test that an adapter with a controller calls the controller cleanup method."""
        with caplog.at_level('DEBUG'):
            try:
                await test_async_api_adapter_with_controller.adapter.cleanup()
            except Exception as exc:
                pytest.fail(f"Adapter cleanup raised an exception: {exc}")
            assert any(record.levelname == 'DEBUG' for record in caplog.records)
            assert (f"{test_async_api_adapter_with_controller.adapter.name} cleanup called" in
                    caplog.text)

    @pytest.mark.parametrize("with_metadata", [False, True])
    @pytest.mark.asyncio
    async def test_async_adapter_with_controller_get(
            self, test_async_api_adapter_with_controller, with_metadata
        ):
        """Test that the controller get method is called and returns the correct response."""
        request = test_async_api_adapter_with_controller.request
        request.headers['Accept'] = f'application/json; metadata={str(with_metadata).lower()}'

        response = await test_async_api_adapter_with_controller.adapter.get(
            test_async_api_adapter_with_controller.path, request
        )
        assert response.data == {
            "response": (
                f"get called on path {test_async_api_adapter_with_controller.path} "
                f"with_metadata={with_metadata}"
            )
        }
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_async_adapter_with_controller_get_error(
            self, test_async_api_adapter_with_controller
        ):
        """Test that the controller get method raises an error and is handled correctly."""
        path = test_async_api_adapter_with_controller.path + '/error'
        response = await test_async_api_adapter_with_controller.adapter.get(
            path, test_async_api_adapter_with_controller.request
        )
        assert response.data == {"error": "Test error raised from controller get method"}
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_async_adapter_with_controller_put(
            self, test_async_api_adapter_with_controller
        ):
        """Test that the controller set method is called and returns the correct response."""
        request = test_async_api_adapter_with_controller.request
        request.data = b'{"key": "value"}'

        response = await test_async_api_adapter_with_controller.adapter.put(
            test_async_api_adapter_with_controller.path,
            test_async_api_adapter_with_controller.request
        )
        assert response.data == {
            "response": (
                f"get called on path {test_async_api_adapter_with_controller.path} with_metadata=False"
            )
        }
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_async_adapter_with_controller_put_error(
            self, test_async_api_adapter_with_controller
        ):
        """Test that the controller set method raises an error and is handled correctly."""
        path = test_async_api_adapter_with_controller.path + '/error'
        request = test_async_api_adapter_with_controller.request
        request.data = b'{"key": "value"}'

        response = await test_async_api_adapter_with_controller.adapter.put(
            path, test_async_api_adapter_with_controller.request
        )
        assert response.data == {"error": "Test error raised from controller set method"}
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_async_adapter_with_controller_put_decode_error(
            self, test_async_api_adapter_with_controller
        ):
        """Test that a decode error in the PUT request body is handled correctly."""
        request = test_async_api_adapter_with_controller.request
        request.body = b'{"key": "value"'  # Malformed JSON

        response = await test_async_api_adapter_with_controller.adapter.put(
            test_async_api_adapter_with_controller.path,
            test_async_api_adapter_with_controller.request
        )
        assert "error" in response.data
        assert "Failed to decode PUT request body" in response.data["error"]
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_async_adapter_with_controller_post(
            self, test_async_api_adapter_with_controller
        ):
        """Test that the controller create method is called and returns the correct response."""
        request = test_async_api_adapter_with_controller.request
        request.body = b'{"key": "value"}'

        response = await test_async_api_adapter_with_controller.adapter.post(
            test_async_api_adapter_with_controller.path,
            test_async_api_adapter_with_controller.request
        )
        assert response.data == {"key": "value"}
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_async_adapter_with_controller_post_error(
            self, test_async_api_adapter_with_controller
        ):
        """Test that the controller create method raises an error and is handled correctly."""
        path = test_async_api_adapter_with_controller.path + '/error'
        request = test_async_api_adapter_with_controller.request
        request.body = b'{"key": "value"}'

        response = await test_async_api_adapter_with_controller.adapter.post(
            path, test_async_api_adapter_with_controller.request
        )
        assert response.data == {"error": "Test error raised from controller create method"}
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_async_adapter_with_controller_post_decode_error(
            self, test_async_api_adapter_with_controller
        ):
        """Test that a decode error in the POST request body is handled correctly."""
        request = test_async_api_adapter_with_controller.request
        request.body = b'{"key": "value"'  # Malformed JSON

        response = await test_async_api_adapter_with_controller.adapter.post(
            test_async_api_adapter_with_controller.path,
            test_async_api_adapter_with_controller.request
        )
        assert "error" in response.data
        assert "Failed to decode POST request body" in response.data["error"]
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_async_adapter_with_controller_delete(
            self, test_async_api_adapter_with_controller
        ):
        """Test that the controller delete method is called and returns the correct response."""
        response = await test_async_api_adapter_with_controller.adapter.delete(
            test_async_api_adapter_with_controller.path,
            test_async_api_adapter_with_controller.request
        )
        assert response.data == {
            "response": f"delete called on path {test_async_api_adapter_with_controller.path}"
        }
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_async_adapter_with_controller_delete_error(
            self, test_async_api_adapter_with_controller
        ):
        """Test that the controller delete method raises an error and is handled correctly."""
        path = test_async_api_adapter_with_controller.path + '/error'

        response = await test_async_api_adapter_with_controller.adapter.delete(
            path, test_async_api_adapter_with_controller.request
        )
        assert response.data == {"error": "Test error raised from controller delete method"}
        assert response.status_code == 400


