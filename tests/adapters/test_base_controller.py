import pytest

from odin_control.adapters.base_controller import BaseController

class DerivedTestController(BaseController):
    def __init__(self, options):
        super().__init__(options)
        self.options = options

    def initialize(self, adapters):
        super().initialize(adapters)

    def get(self, path, with_metadata = False):

        return {"path": path, "with_metadata": with_metadata}

    def cleanup(self):
        super().cleanup()
        self.options = None
        self.adapters = None

@pytest.fixture
def derived_test_controller():

    test_controller = DerivedTestController(options={})
    yield test_controller

class TestBaseController:

    def test_base_controller_is_abstract(self):
        """Test that BaseController cannot be instantiated directly."""
        from odin_control.adapters.base_controller import BaseController

        with pytest.raises(TypeError) as excinfo:
            BaseController({})

        assert "Can't instantiate abstract class BaseController" in str(excinfo.value)

    def test_derived_controller_initizialization(self, derived_test_controller):
        """Test that DerivedTestController initializes adapter info correctly."""
        adapters = {"test_adapter": object(), "another_adapter": object()}
        derived_test_controller.initialize(adapters)

        assert "test_adapter" in derived_test_controller.adapters
        assert "another_adapter" in derived_test_controller.adapters

    def test_derived_controller_get_method(self, derived_test_controller):
        """Test that DerivedTestController get method works as expected."""
        path = "/test/path"
        result = derived_test_controller.get(path, with_metadata=True)

        assert result["path"] == path
        assert result["with_metadata"] is True

    def test_derived_controller_cleanup(self, derived_test_controller):
        """Test that DerivedTestController cleanup method resets state."""
        adapters = {"test_adapter": object()}
        derived_test_controller.initialize(adapters)

        derived_test_controller.cleanup()

        assert derived_test_controller.options is None
        assert derived_test_controller.adapters is None

    def test_derived_controller_set_not_implemented(self, derived_test_controller):
        """Test that DerivedTestController set method raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            derived_test_controller.set("/test/path", {"key": "value"})

    def test_derived_controller_create_not_implemented(self, derived_test_controller):
        """Test that DerivedTestController create method raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            derived_test_controller.create("/test/path", {"key": "value"})

    def test_derived_controller_delete_not_implemented(self, derived_test_controller):
        """Test that DerivedTestController delete method raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            derived_test_controller.delete("/test/path")
