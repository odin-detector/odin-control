import sys

import pytest

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock
else:                         # pragma: no cover
    from mock import Mock

from odin.adapters.adapter import (ApiAdapter, ApiAdapterResponse, ApiAdapterRequest,
                                   request_types, response_types, wants_metadata)

class ApiAdapterTestFixture(object):
    """ Container class used in fixtures for testing ApiAdapter behaviour."""
    def __init__(self):
        self.adapter_options = {
            'test_option_float' : 1.234,
            'test_option_str' : 'value',
            'test_option_int' : 4567.
        }
        self.adapter = ApiAdapter(**self.adapter_options)
        self.path = '/api/path'
        self.request = Mock()
        self.request.headers = {'Accept': '*/*', 'Content-Type': 'text/plain'}

@pytest.fixture(scope="class")
def test_api_adapter():
    """Simple test fixture used for testing ApiAdapter."""
    test_api_adapter = ApiAdapterTestFixture()
    yield test_api_adapter

class TestApiAdapter():
    """Class to test the ApiAdapter object."""

    def test_adapter_get(self, test_api_adapter):
        """
        Test the the adapter responds to a GET request correctly by returning a 400 code and
        appropriate message. This is due to the base adapter not implementing the methods.
        """
        response = test_api_adapter.adapter.get(test_api_adapter.path, test_api_adapter.request)
        assert response.data == 'GET method not implemented by ApiAdapter'
        assert response.status_code == 400

    def test_adapter_put(self, test_api_adapter):
        """
        Test the the adapter responds to a PUT request correctly by returning a 400 code and
        appropriate message. This is due to the base adapter not implementing the methods.
        """
        response = test_api_adapter.adapter.put(test_api_adapter.path, test_api_adapter.request)
        assert response.data == 'PUT method not implemented by ApiAdapter'
        assert response.status_code == 400

    def test_adapter_delete(self, test_api_adapter):
        """
        Test the the adapter responds to a DELETE request correctly by returning a 400 code and
        appropriate message. This is due to the base adapter not implementing the methods.
        """
        response = test_api_adapter.adapter.delete(test_api_adapter.path, test_api_adapter.request)
        assert response.data == 'DELETE method not implemented by ApiAdapter'
        assert response.status_code == 400

    def test_api_adapter_has_options(self, test_api_adapter):
        """Test that the adapter loads the options correctly."""
        opts = test_api_adapter.adapter.options
        assert opts == test_api_adapter.adapter_options

    def test_api_adapter_cleanup(self, test_api_adapter):
        """Test the the adapter cleanup function runs without error."""
        raised = False
        try:
            test_api_adapter.adapter.cleanup()
        except:
            raised = True
        assert not raised

    def test_api_adapter_initialize(self, test_api_adapter):
        """Test the the adapter initialize function runs without error."""
        raised = False
        try:
            test_api_adapter.adapter.initialize(None)
        except:
            raised = True
        assert not raised


class TestAdapterRequest():
    """Class to test behaviour of the AdapterRequest object."""

    def test_simple_request(self):
        """Test that a simple request is populated with the correct fields."""
        data = "This is some simple request data"
        request = ApiAdapterRequest(data)
        assert request.body == data
        assert request.content_type == 'application/vnd.odin-native'
        assert request.response_type == "application/json"
        expected_headers = {
            "Content-Type": 'application/vnd.odin-native',
            "Accept": "application/json"
        }
        assert request.headers == expected_headers

    def test_request_with_types(self):
        """Test that a request with the correct types is correctly populated."""
        data = '{\'some_json_value\' : 1.234}'
        content_type = 'application/json'
        request_type = "application/vnd.odin-native"
        request = ApiAdapterRequest(data, content_type=content_type, accept=request_type)
        assert request.body == data
        assert request.content_type == content_type
        assert request.response_type == request_type
        assert request.headers == {
            "Content-Type": content_type,
            "Accept": request_type}


    def test_set_content(self):
        """Test that explicitly setting fields on the request works correctly."""
        data = '{\'some_json_value\' : 1.234}'
        content_type = 'application/json'
        request_type = "application/vnd.odin-native"
        remote_ip = "127.0.0.1"

        request = ApiAdapterRequest(data)
        request.set_content_type(content_type)
        request.set_response_type(request_type)
        request.set_remote_ip(remote_ip)

        assert request.body == data
        assert request.content_type == content_type
        assert request.response_type == request_type
        assert request.remote_ip == remote_ip
        assert request.headers == {
            "Content-Type": content_type,
            "Accept": request_type}

    def test_wants_metadata(self):
        """Test that the wants_metadata fields on the rqeuest object works correctly."""
        request = Mock()
        for metadata_state in (True, False):
            request.headers = {
                'Accept': 'application/json;metadata={}'.format(str(metadata_state))
            }
            assert wants_metadata(request) == metadata_state

            request.headers = {
                'Accept': 'application/json;metadata={}'.format(str(metadata_state).lower())
            }
            assert wants_metadata(request) == metadata_state

        request.headers = {'Accept:' 'application/json;metadata=wibble'}
        assert not wants_metadata(request)

class TestApiAdapterResponse():
    """Class to test behaviour of the ApiAdapterResponse object."""

    def test_simple_response(self):
        """Test that a simple rewponse contains the correct default values in fields."""
        data = 'This is a simple response'
        response = ApiAdapterResponse(data)

        assert response.data == data
        assert response.content_type == 'text/plain'
        assert response.status_code == 200

    def test_response_with_type_and_code(self):
        """
        Test that a response with explicit content type and status codes 
        correctly populates the fields.
        """
        data = '{\'some_json_value\' : 1.234}'
        content_type = 'application/json'
        status_code = 400

        response = ApiAdapterResponse(data, content_type=content_type, status_code=status_code)
        assert response.data == data
        assert response.content_type == content_type
        assert response.status_code == status_code

    def test_response_with_set_calls(self):
        """
        Test the creating a default response and then explicitly setting the type and code 
        correctly populates the fields.
        """
        data = '{\'some_json_value\' : 1.234}'
        content_type = 'application/json'
        status_code = 400

        response = ApiAdapterResponse(data)
        response.set_content_type(content_type)
        response.set_status_code(status_code)

        assert response.data == data
        assert response.content_type == content_type
        assert response.status_code == status_code


class ApiMethodDecoratorsTestFixture(object):
    """Container class used in fixtures for testing adapter method decorators."""

    def __init__(self):
        """Initialise request and responses for testing method decorators."""
        self.path = '/api/path'
        self.response_code = 200
        self.response_type_plain = 'text/plain'
        self.response_data_plain = 'Plain text response'

        self.response_type_json = 'application/json'
        self.response_data_json = {'response': 'JSON response'}

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


@pytest.fixture(scope="class")
def test_api_decorator():
    """Test fixture for testing method decorators."""
    test_api_decorator = ApiMethodDecoratorsTestFixture()
    yield test_api_decorator

class TestApiMethodDecorators(object):
    """Class to test API method decorators."""

    def test_decorated_method_plaintext(self, test_api_decorator):
        """ Test that a method being passed a plaintext request responds correctly."""
        plain_request = Mock()
        plain_request.data = 'Simple plain text request'
        plain_request.headers = {'Accept': 'text/plain', 'Content-Type': 'text/plain'}

        response = test_api_decorator.decorated_method(test_api_decorator.path, plain_request)
        assert response.status_code == test_api_decorator.response_code
        assert response.content_type == test_api_decorator.response_type_plain
        assert response.data == test_api_decorator.response_data_plain

    def test_decorated_method_default(self, test_api_decorator):
        """
        Test that a decorated method being passed a JSON object responds correctly when 
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
        """
        Test that a decorated method being passed a JSON object responds correctly when 
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
        """
        Test that a decorated method with no default defined returns a response matching the
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
        """
        Test that a decorated method with no default defined returns a JSON repsonse to a JSON
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
        """
        Test that a decorated method responds to a request with no Accept header with the
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
        """
        Test that a decorated method with no default responsds 
        """
        request = Mock()
        request.data = 'Some text'
        request.headers = {'Content-Type': 'text/plain'}

        response = test_api_decorator.decorated_method_without_default(test_api_decorator.path, request)
        assert response.status_code == test_api_decorator.response_code
        assert response.content_type == test_api_decorator.response_type_plain
        assert response.data == test_api_decorator.response_data_plain
