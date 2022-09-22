import sys
import json

import pytest

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock
else:                         # pragma: no cover
    from mock import Mock

from odin.http.routes.api import ApiRoute, ApiHandler, ApiError, API_VERSION
from odin.config.parser import AdapterConfig

@pytest.fixture(scope="class")
def test_api_route():
    """Simple test fixture that creates an ApiRoute object."""
    ar = ApiRoute(enable_cors=True, cors_origin="*")
    yield ar

class TestApiRoute(object):
    """Class to test the behaviour of the ApiRoute."""

    def test_api_route_has_handlers(self, test_api_route):
        """Test that the default ApiRoute object has handlers."""
        assert len(test_api_route.get_handlers()) > 0

    def test_register_adapter(self, test_api_route):
        """Test that it is possible to register an adapter with the API route object."""
        adapter_config = AdapterConfig('dummy', 'odin.adapters.dummy.DummyAdapter')
        test_api_route.register_adapter(adapter_config)

        assert test_api_route.has_adapter('dummy')

    def test_register_adapter_badmodule(self, test_api_route):
        """Test that registering an adapter with a bad module name raises an error."""
        adapter_name = 'dummy'
        adapter_config = AdapterConfig(adapter_name, 'odin.adapters.bad_dummy.DummyAdapter')

        with pytest.raises(ApiError) as excinfo:
            test_api_route.register_adapter(adapter_config, fail_ok=False)

            assert 'No module named {}'.format(adapter_name) in str(excinfo.value)

    def test_register_adapter_badclass(self, test_api_route):
        """Test that registering an adapter with a bad class name raises an error."""
        adapter_config = AdapterConfig('dummy', 'odin.adapters.dummy.BadAdapter')

        with pytest.raises(ApiError) as excinfo:
            test_api_route.register_adapter(adapter_config, fail_ok=False)

        assert 'has no attribute \'BadAdapter\'' in str(excinfo.value)

    def test_register_adapter_no_cleanup(self, test_api_route):
        """
        Test that attempting to clean up an adapter without a cleanup method doesn't 
        cause an error
        """
        adapter_name = 'dummy_no_clean'
        adapter_config = AdapterConfig(adapter_name, 'odin.adapters.dummy.DummyAdapter')
        test_api_route.register_adapter(adapter_config)
        test_api_route.adapters[adapter_name].cleanup = Mock(side_effect=AttributeError())

        raised = False
        try:
            test_api_route.cleanup_adapters()
        except:
            raised = True

        assert not raised

    def test_register_adapter_no_initialize(self, test_api_route):
        """
        Test that attempting to inialize an adapter without an initialize method doesn't
        raise an error.
        """
        adapter_name = 'dummy_no_clean'
        adapter_config = AdapterConfig(adapter_name, 'odin.adapters.dummy.DummyAdapter')
        test_api_route.register_adapter(adapter_config)
        test_api_route.adapters[adapter_name].initialize = Mock(side_effect=AttributeError())

        raised = False
        try:
            test_api_route.initialize_adapters()
        except:
            raised = True

        assert not raised

