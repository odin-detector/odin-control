"""Test cases for ODIN API adapter request classes."""

from odin_control.adapters.request import ApiAdapterRequest


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
