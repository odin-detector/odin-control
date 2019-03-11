import sys

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock
else:                         # pragma: no cover
    from mock import Mock

from nose.tools import *

from odin.adapters.adapter import (ApiAdapter, ApiAdapterResponse, ApiAdapterRequest,
                                   request_types, response_types, wants_metadata)

class TestApiAdapter():

    @classmethod
    def setup_class(cls):

        cls.adapter_options = {
            'test_option_float' : 1.234,
            'test_option_str' : 'value',
            'test_option_int' : 4567.
        }
        cls.adapter = ApiAdapter(**cls.adapter_options)
        cls.path = '/api/path'
        cls.request = Mock()
        cls.request.headers = {'Accept': '*/*', 'Content-Type': 'text/plain'}

    def test_adapter_get(self):
        response = self.adapter.get(self.path, self.request)
        assert_equal(response.data, 'GET method not implemented by ApiAdapter')
        assert_equal(response.status_code, 400)


    def test_adapter_put(self):
        response = self.adapter.put(self.path, self.request)
        assert_equal(response.data, 'PUT method not implemented by ApiAdapter')
        assert_equal(response.status_code, 400)


    def test_adapter_delete(self):
        response = self.adapter.delete(self.path, self.request)
        assert_equal(response.data, 'DELETE method not implemented by ApiAdapter')
        assert_equal(response.status_code, 400)

    def test_api_adapter_has_options(self):

        opts = self.adapter.options
        assert_equal(opts, self.adapter_options)

    def test_api_adapter_cleanup(self):

        raised = False
        try:
            self.adapter.cleanup()
        except:
            raised = True
        assert_false(raised)

    def test_api_adapter_initialize(self):
        
        raised = False
        try:
            self.adapter.initialize(None)
        except:
            raised = True
        assert_false(raised)


class TestAdapterRequest():

    def test_simple_request(self):
        data = "This is some simple request data"
        request = ApiAdapterRequest(data)
        assert_equal(request.body, data)
        assert_equal(request.content_type, 'application/vnd.odin-native')
        assert_equal(request.response_type, "application/json")
        expected_headers = {
            "Content-Type": 'application/vnd.odin-native',
            "Accept": "application/json"
        }
        assert_equal(request.headers, expected_headers)

    def test_request_with_types(self):
        data = '{\'some_json_value\' : 1.234}'
        content_type = 'application/json'
        request_type = "application/vnd.odin-native"
        request = ApiAdapterRequest(data, content_type=content_type, accept=request_type)
        assert_equal(request.body, data)
        assert_equal(request.content_type, content_type)
        assert_equal(request.response_type, request_type)
        assert_equal(request.headers, {
            "Content-Type": content_type,
            "Accept": request_type})

    def test_set_content(self):
        data = '{\'some_json_value\' : 1.234}'
        content_type = 'application/json'
        request_type = "application/vnd.odin-native"
        remote_ip = "127.0.0.1"

        request = ApiAdapterRequest(data)
        request.set_content_type(content_type)
        request.set_response_type(request_type)
        request.set_remote_ip(remote_ip)

        assert_equal(request.body, data)
        assert_equal(request.content_type, content_type)
        assert_equal(request.response_type, request_type)
        assert_equal(request.remote_ip, remote_ip)
        assert_equal(request.headers, {
            "Content-Type": content_type,
            "Accept": request_type})

    def test_wants_metadata(self):

        request = Mock()
        for metadata_state in (True, False):
            request.headers = {
                'Accept': 'application/json;metadata={}'.format(str(metadata_state))
            }
            assert_equal(wants_metadata(request), metadata_state)

            request.headers = {
                'Accept': 'application/json;metadata={}'.format(str(metadata_state).lower())
            }
            assert_equal(wants_metadata(request), metadata_state)

        request.headers = {'Accept:' 'application/json;metadata=wibble'}
        assert_equal(wants_metadata(request), False)

class TestApiAdapterResponse():

    def test_simple_response(self):

        data = 'This is a simple response'
        response = ApiAdapterResponse(data)

        assert_equal(response.data, data)
        assert_equal(response.content_type, 'text/plain')
        assert_equal(response.status_code, 200)

    def test_response_with_type_and_code(self):

        data = '{\'some_json_value\' : 1.234}'
        content_type = 'application/json'
        status_code = 400

        response = ApiAdapterResponse(data, content_type=content_type, status_code=status_code)
        assert_equal(response.data, data)
        assert_equal(response.content_type, content_type)
        assert_equal(response.status_code, status_code)

    def test_response_with_set_calls(self):

        data = '{\'some_json_value\' : 1.234}'
        content_type = 'application/json'
        status_code = 400

        response = ApiAdapterResponse(data)
        response.set_content_type(content_type)
        response.set_status_code(status_code)

        assert_equal(response.data, data)
        assert_equal(response.content_type, content_type)
        assert_equal(response.status_code, status_code)


class TestApiMethodDecorators():

    @classmethod
    def setup_class(cls):

        cls.path = '/api/path'
        cls.response_code = 200
        cls.response_type_plain = 'text/plain'
        cls.response_data_plain = 'Plain text response'

        cls.response_type_json = 'application/json'
        cls.response_data_json = {'response': 'JSON response'}

    @request_types('application/json', 'text/plain')
    @response_types('application/json', 'text/plain', default='application/json')
    def decorated_method(self, path, request):

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

    def test_decorated_method_plaintext(self):

        plain_request = Mock()
        plain_request.data = 'Simple plain text request'
        plain_request.headers = {'Accept': 'text/plain', 'Content-Type': 'text/plain'}

        response = self.decorated_method(self.path, plain_request)
        assert_equal(response.status_code, self.response_code)
        assert_equal(response.content_type, self.response_type_plain)
        assert_equal(response.data, self.response_data_plain)

    def test_decorated_method_default(self):

        json_request = Mock()
        json_request.data = '{\'request\': 1234}'
        json_request.headers = {'Accept': '*/*', 'Content-Type': 'application/json'}

        response = self.decorated_method(self.path, json_request)
        assert_equal(response.status_code, self.response_code)
        assert_equal(response.content_type, self.response_type_json)
        assert_equal(response.data, self.response_data_json)

    def test_decorated_method_json(self):

        json_request = Mock()
        json_request.data = '{\'request\' : 1234}'
        json_request.headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

        response = self.decorated_method(self.path, json_request)
        assert_equal(response.status_code, self.response_code)
        assert_equal(response.content_type, self.response_type_json)
        assert_equal(response.data, self.response_data_json)

    def test_decorated_method_bad_content(self):

        json_request = Mock()
        json_request.data = 'wibble'
        json_request.headers = {'Accept': 'application/json', 'Content-Type': 'application/hdf'}

        response = self.decorated_method(self.path, json_request)
        assert_equal(response.status_code, 415)
        assert_equal(response.data, 'Request content type (application/hdf) not supported')

    def test_decorated_method_bad_accept(self):

        request = Mock()
        request.data = 'Some text'
        request.headers = {'Accept': 'application/hdf', 'Content-Type': 'text/plain'}

        response = self.decorated_method(self.path, request)
        assert_equal(response.status_code, 406)
        assert_equal(response.data, 'Requested content types not supported')

    def test_decorated_method_no_default(self):

        request = Mock()
        request.data = 'Some text'
        request.headers = {'Accept': '*/*', 'Content-Type': 'text/plain'}

        response = self.decorated_method_without_default(self.path, request)
        assert_equal(response.status_code, self.response_code)
        assert_equal(response.content_type, self.response_type_plain)
        assert_equal(response.data, self.response_data_plain)

    def test_decorated_method_no_default_json(self):

        request = Mock()
        request.data = '{\'request\' : 1234}'
        request.headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

        response = self.decorated_method_without_default(self.path, request)
        assert_equal(response.status_code, self.response_code)
        assert_equal(response.content_type, self.response_type_json)
        assert_equal(response.data, self.response_data_json)

    def test_decorated_method_no_accept(self):

        request = Mock()
        request.data = 'Some text'
        request.headers = {'Content-Type': 'text/plain'}

        response = self.decorated_method(self.path, request)
        assert_equal(response.status_code, self.response_code)
        assert_equal(response.content_type, self.response_type_json)
        assert_equal(response.data, self.response_data_json)

    def test_decorated_method_no_accept_no_default(self):

        request = Mock()
        request.data = 'Some text'
        request.headers = {'Content-Type': 'text/plain'}

        response = self.decorated_method_without_default(self.path, request)
        assert_equal(response.status_code, self.response_code)
        assert_equal(response.content_type, self.response_type_plain)
        assert_equal(response.data, self.response_data_plain)
