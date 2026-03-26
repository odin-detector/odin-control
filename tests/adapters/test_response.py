"""Test cases for ODIN API adapter response classes."""

from odin_control.adapters.response import ApiAdapterResponse


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
