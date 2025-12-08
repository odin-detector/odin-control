import pytest

from odin_control.adapters.async_base_controller import AsyncBaseController


class DerivedAsyncTestController(AsyncBaseController):
    def __init__(self, options):
        super().__init__(options)
        self.options = options
        self.awaited = False

        async def awaitable_attribute():
            self.awaited = True
            return "awaited value"

        self.awaited_value = awaitable_attribute()

    async def initialize(self, adapters):
        await super().initialize(adapters)

    async def get(self, path, with_metadata = False):

        return {"path": path, "with_metadata": with_metadata, "value": self.awaited_value}

    async def cleanup(self):
        await super().cleanup()
        self.options = None
        self.adapters = None

@pytest.fixture
def derived_async_test_controller():

    return DerivedAsyncTestController(options={})

class TestAsyncBaseController:

    def test_async_base_controller_is_abstract(self):
        """Test that AsyncBaseController cannot be instantiated directly."""
        from odin_control.adapters.async_base_controller import AsyncBaseController

        with pytest.raises(TypeError) as excinfo:
            AsyncBaseController({})

        assert "Can't instantiate abstract class AsyncBaseController" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_async_controller_awaitable_init(self):
        """Test that AsyncBaseController derived class can be awaited to resolve async attributes."""
        controller = await DerivedAsyncTestController(options={})
        assert controller.awaited

    @pytest.mark.asyncio
    async def test_derived_async_controller_initialization(self, derived_async_test_controller):
        """Test that DerivedAsyncTestController initializes adapter info correctly."""
        adapters = {"test_adapter": object(), "another_adapter": object()}
        derived_async_test_controller = await derived_async_test_controller
        await derived_async_test_controller.initialize(adapters)
        assert "test_adapter" in derived_async_test_controller.adapters
        assert "another_adapter" in derived_async_test_controller.adapters

    @pytest.mark.asyncio
    async def test_derived_async_controller_get_method(self, derived_async_test_controller):
        """Test that DerivedAsyncTestController get method works as expected."""
        derived_async_test_controller = await derived_async_test_controller

        path = "/test/path"
        result = await derived_async_test_controller.get(path, with_metadata=True)

        assert result["path"] == path
        assert result["with_metadata"] is True

    @pytest.mark.asyncio
    async def test_derived_async_controller_cleanup(self, derived_async_test_controller):
        """Test that DerivedAsyncTestController cleanup method resets state."""
        derived_async_test_controller = await derived_async_test_controller

        adapters = {"test_adapter": object()}
        await derived_async_test_controller.initialize(adapters)
        await derived_async_test_controller.cleanup()

        assert derived_async_test_controller.options is None
        assert derived_async_test_controller.adapters is None

    @pytest.mark.asyncio
    async def test_derived_controller_set_not_implemented(self, derived_async_test_controller):
        """Test that DerivedAsyncTestController set method raises NotImplementedError."""
        derived_async_test_controller = await derived_async_test_controller

        with pytest.raises(NotImplementedError):
            await derived_async_test_controller.set("/test/path", data={})

    @pytest.mark.asyncio
    async def test_derived_controller_create_not_implemented(self, derived_async_test_controller):
        """Test that DerivedAsyncTestController create method raises NotImplementedError."""
        derived_async_test_controller = await derived_async_test_controller

        with pytest.raises(NotImplementedError):
            await derived_async_test_controller.create("/test/path", data={})

    @pytest.mark.asyncio
    async def test_derived_controller_delete_not_implemented(self, derived_async_test_controller):
        """Test that DerivedAsyncTestController delete method raises NotImplementedError."""
        derived_async_test_controller = await derived_async_test_controller

        with pytest.raises(NotImplementedError):
            await derived_async_test_controller.delete("/test/path")


