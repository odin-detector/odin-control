from unittest.mock import Mock

import pytest
from tornado.concurrent import Future

from odin_control.adapters.response import ApiAdapterResponse
from odin_control.adapters.util import (
    request_types,
    require_controller,
    response_types,
    wants_metadata,
    wrap_result,
)


class TestWrapResult():
    """Class to test the wrap_result utility function."""

    def test_wrap_result_sync(self):
        """Test that wrap_result returns the result directly when async is False."""
        result = 123
        wrapped = wrap_result(result, False)
        assert wrapped == result

    def test_wrap_result_async(self):
        """Test that wrap_result correctly wraps results in a future when async is True."""
        result = 123
        wrapped = wrap_result(result, True)
        assert isinstance(wrapped, Future)
        assert wrapped.result() == result

    @pytest.mark.asyncio
    async def test_awaited_wrap_result(self):
        """Test that wrap_result returns an awaitable future when async is True."""
        result = 123
        wrapped = wrap_result(result, True)
        assert isinstance(wrapped, Future)
        awaited_result = await wrapped
        assert awaited_result == result


class ApiMethodDecoratorsTestFixture():
    """Container class used in fixtures for testing adapter method decorators."""

    def __init__(self, with_controller=False):
        """Initialise request and responses for testing method decorators."""

        self.name = "test"
        self.path = '/api/path'
        self.response_code = 200
        self.response_type_plain = 'text/plain'
        self.response_data_plain = 'Plain text response'

        self.response_type_json = 'application/json'
        self.response_data_json = {'response': 'JSON response'}

        self.is_async = False

        if with_controller:
            self.controller = Mock()
        else:
            self.controller = None

    @request_types('application/json', 'text/plain')
    @response_types('application/json', 'text/plain', default='application/json')
    def decorated_method(self, path, request):
        """Decorated method having defined request, response and default types."""
        if request.headers['Accept'] == self.response_type_plain:
            response = ApiAdapterResponse(
                self.response_data_plain,
                content_type=self.response_type_plain, status_code=self.response_code)
        else:
            response = ApiAdapterResponse(
                self.response_data_json,
                content_type=self.response_type_json, status_code=self.response_code)

        return response

    @request_types('application/json', 'text/plain')
    @response_types('application/json')
    def decorated_method_without_default(self, path, request):
        """Decorated method having defined request, response but no default type."""
        if request.headers['Accept'] == self.response_type_plain:
            response = ApiAdapterResponse(
                self.response_data_plain,
                content_type=self.response_type_plain, status_code=self.response_code)
        elif request.headers['Accept'] == '*/*':
            response = ApiAdapterResponse(
                self.response_data_plain,
                content_type=self.response_type_plain, status_code=self.response_code)
        elif request.headers['Accept'] == self.response_type_json:
            response = ApiAdapterResponse(
                self.response_data_json,
                content_type=self.response_type_json, status_code=self.response_code)
        else:  # pragma: no cover
            response = None
            assert ("Request type decorator failed to trap unknown content type")

        return response

    @require_controller
    def decorated_method_for_controller(self, path, request):
        """Method decorated to require a controller."""
        return ApiAdapterResponse(
            self.response_data_json, content_type=self.response_type_json,
            status_code=self.response_code
        )

@pytest.fixture(scope="class")
def test_api_decorator():
    """Test fixture for testing method decorators."""
    test_api_decorator = ApiMethodDecoratorsTestFixture()
    yield test_api_decorator

@pytest.fixture(scope="class")
def test_api_decorator_with_controller():
    """Test fixture for testing method decorators with a controller."""
    test_api_decorator = ApiMethodDecoratorsTestFixture(with_controller=True)
    yield test_api_decorator

class TestApiMethodDecorators():
    """Class to test API method decorators."""

    def test_decorated_method_plaintext(self, test_api_decorator):
        """Test that a method being passed a plaintext request responds correctly."""
        plain_request = Mock()
        plain_request.data = 'Simple plain text request'
        plain_request.headers = {'Accept': 'text/plain', 'Content-Type': 'text/plain'}

        response = test_api_decorator.decorated_method(test_api_decorator.path, plain_request)
        assert response.status_code == test_api_decorator.response_code
        assert response.content_type == test_api_decorator.response_type_plain
        assert response.data == test_api_decorator.response_data_plain

    def test_decorated_method_default(self, test_api_decorator):
        """Test that a decorated method being passed a JSON object responds correctly when
        the accepted type is default.
        """
        json_request = Mock()
        json_request.data = '{\'request\': 1234}'
        json_request.headers = {'Accept': '*/*', 'Content-Type': 'application/json'}

        response = test_api_decorator.decorated_method(test_api_decorator.path, json_request)
        assert response.status_code == test_api_decorator.response_code
        assert response.content_type == test_api_decorator.response_type_json
        assert response.data == test_api_decorator.response_data_json

    def test_decorated_method_json(self, test_api_decorator):
        """Test that a decorated method being passed a JSON object responds correctly when
        the accepted type is also JSON.
        """
        json_request = Mock()
        json_request.data = '{\'request\' : 1234}'
        json_request.headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

        response = test_api_decorator.decorated_method(test_api_decorator.path, json_request)
        assert response.status_code == test_api_decorator.response_code
        assert response.content_type == test_api_decorator.response_type_json
        assert response.data == test_api_decorator.response_data_json

    def test_decorated_method_bad_content(self, test_api_decorator):
        """Test that a decorated method passed an unsupported content type returns an error."""
        json_request = Mock()
        json_request.data = 'wibble'
        json_request.headers = {'Accept': 'application/json', 'Content-Type': 'application/hdf'}

        response = test_api_decorator.decorated_method(test_api_decorator.path, json_request)
        assert response.status_code == 415
        assert response.data == 'Request content type (application/hdf) not supported'

    def test_decorated_method_bad_accept(self, test_api_decorator):
        """Test that a decorated method passed an unsupported accept type returns an error."""
        request = Mock()
        request.data = 'Some text'
        request.headers = {'Accept': 'application/hdf', 'Content-Type': 'text/plain'}

        response = test_api_decorator.decorated_method(test_api_decorator.path, request)
        assert response.status_code == 406
        assert response.data == 'Requested content types not supported'

    def test_decorated_method_no_default(self, test_api_decorator):
        """Test that a decorated method with no default defined returns a response matching the
        request.
        """
        request = Mock()
        request.data = 'Some text'
        request.headers = {'Accept': '*/*', 'Content-Type': 'text/plain'}

        response = test_api_decorator.decorated_method_without_default(test_api_decorator.path, request)
        assert response.status_code == test_api_decorator.response_code
        assert response.content_type == test_api_decorator.response_type_plain
        assert response.data == test_api_decorator.response_data_plain

    def test_decorated_method_no_default_json(self, test_api_decorator):
        """Test that a decorated method with no default defined returns a JSON repsonse to a JSON
        request.
        """
        request = Mock()
        request.data = '{\'request\' : 1234}'
        request.headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

        response = test_api_decorator.decorated_method_without_default(test_api_decorator.path, request)
        assert response.status_code == test_api_decorator.response_code
        assert response.content_type == test_api_decorator.response_type_json
        assert response.data == test_api_decorator.response_data_json

    def test_decorated_method_no_accept(self, test_api_decorator):
        """Test that a decorated method responds to a request with no Accept header with the
        appropriate default response type.
        """
        request = Mock()
        request.data = 'Some text'
        request.headers = {'Content-Type': 'text/plain'}

        response = test_api_decorator.decorated_method(test_api_decorator.path, request)
        assert response.status_code == test_api_decorator.response_code
        assert response.content_type == test_api_decorator.response_type_json
        assert response.data == test_api_decorator.response_data_json

    def test_decorated_method_no_accept_no_default(self, test_api_decorator):
        """Test that a decorated method with no default responsds
        """
        request = Mock()
        request.data = 'Some text'
        request.headers = {'Content-Type': 'text/plain'}

        response = test_api_decorator.decorated_method_without_default(test_api_decorator.path, request)
        assert response.status_code == test_api_decorator.response_code
        assert response.content_type == test_api_decorator.response_type_plain
        assert response.data == test_api_decorator.response_data_plain

    def test_method_require_controller_no_controller(self, test_api_decorator):
        """Test that a method decorated with require_controller returns an error response
        when no controller is present.
        """
        request = Mock()
        request.data = '{\'request\' : 1234}'
        request.headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

        response = test_api_decorator.decorated_method_for_controller(
            test_api_decorator.path, request)
        assert response.status_code == 405
        assert response.content_type == 'application/json'
        assert response.data == {
            "error": f"Adapter {test_api_decorator.name} has no controller configured"
        }

    def test_method_require_controller_with_controller(self, test_api_decorator_with_controller):
        """Test that a method decorated with require_controller returns a valid response
        when a controller is present.
        """
        request = Mock()
        request.data = '{\'request\' : 1234}'
        request.headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

        response = test_api_decorator_with_controller.decorated_method_for_controller(
            test_api_decorator_with_controller.path, request)
        assert response.status_code == test_api_decorator_with_controller.response_code
        assert response.content_type == test_api_decorator_with_controller.response_type_json
        assert response.data == test_api_decorator_with_controller.response_data_json

class TestWantsMetadata():
    """Class to test the wants_metadata utility function."""

    @pytest.mark.parametrize("metadata", [True, False])
    def test_wants_metadata(self, metadata):
        """Test that wants_metadata returns the appropriate value according to the header."""
        request = Mock()

        for metadata_state in [f(str(metadata)) for f in (str.upper, str.lower, str.capitalize)]:
            request.headers = {'Accept': f'application/json; metadata={metadata_state}'}
            assert wants_metadata(request) == metadata

    def test_wants_metadata_invalid(self):
        """Test that wants_metadata returns False when an invalid metadata value is given."""
        request = Mock()
        request.headers = {'Accept': 'application/json;metadata=wibble'}
        assert not wants_metadata(request)

    def test_wants_metadata_missing(self):
        """Test that wants_metadata returns False when no metadata parameter is given."""
        request = Mock()
        request.headers = {'Accept': 'application/json'}
        assert not wants_metadata(request)

    def test_wants_metadata_no_accept(self):
        """Test that wants_metadata returns False when no Accept header is given."""
        request = Mock()
        request.headers = {}
        assert not wants_metadata(request)
