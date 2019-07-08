import sys
import pytest

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock
else:                         # pragma: no cover
    from mock import Mock

from odin import util

class TestUtil():
    """Class to test utility functions in odin.util"""

    def test_decode_request_body(self):
        """Test that the body a a request is correctly decoded."""
        request = Mock
        request.headers = {'Content-Type': 'application/json'}
        request.body = '{"pi":2.56}'
        response = util.decode_request_body(request)
        assert response == {"pi": 2.56}

    def test_decode_request_body_not_json(self):
        """Test that the body of a native request is correctly decoded."""
        request = Mock
        request.headers = {'Content-Type': 'application/vnd.odin-native'}
        request.body = {"pi": 2.56}
        response = util.decode_request_body(request)
        assert response == request.body

    def test_decode_request_body_type_error(self):
        """Test that a body type mismatch returns the body unchanged."""
        request = Mock
        request.headers = {'Content-Type': 'application/json'}
        request.body = {"pi": 2.56}
        response = util.decode_request_body(request)
        assert response == request.body

    def test_convert_unicode_to_string(self):
        """Test conversion of unicode to string."""
        u_string = u'test string'
        result = util.convert_unicode_to_string(u_string)
        assert result == "test string"

    def test_convert_unicode_to_string_list(self):
        """Test conversion of a list of unicode strings to strings."""
        u_list = [u'first string', u'second string']
        result = util.convert_unicode_to_string(u_list)
        assert result == ["first string", "second string"]

    def test_convert_unicode_to_string_dict(self):
        """Test conversion of a unicode dict to native string dict."""
        u_dict = {u'key': u'value'}
        result = util.convert_unicode_to_string(u_dict)
        assert result == {"key": "value"}

    def test_convert_unicode_to_string_mixed_recursion(self):
        """Test recursion through a deeper object with mixed types."""
        u_object = {u'string': u'test string',
                    u'list': [u'unicode string', "normal string"]
                    }
        result = util.convert_unicode_to_string(u_object)
        expected_result = {
                            'string': 'test string',
                            'list': ['unicode string', "normal string"]
                          }
        assert result == expected_result
