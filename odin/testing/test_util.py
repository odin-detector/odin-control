import sys

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock, patch
else:                         # pragma: no cover
    from mock import Mock, patch

from nose.tools import assert_true, assert_equal

from odin import util

class TestUti():

    def test_decode_request_body(self):
        request = Mock
        request.headers = {'Content-Type': 'application/json'}
        request.body = '{"pi":2.56}'
        response = util.decode_request_body(request)
        assert_equal(response, {"pi": 2.56})

    def test_decode_request_body_not_json(self):
        request = Mock
        request.headers = {'Content-Type': 'application/vnd.odin-native'}
        request.body = {"pi": 2.56}
        response = util.decode_request_body(request)
        assert_equal(response, request.body)

    def test_decode_request_body_type_error(self):
        request = Mock
        request.headers = {'Content-Type': 'application/json'}
        request.body = {"pi": 2.56}
        response = util.decode_request_body(request)
        assert_equal(response, request.body)

    def test_convert_unicode_to_string(self):
        u_string = u'test string'
        result = util.convert_unicode_to_string(u_string)
        assert_equal(result, "test string")

    def test_convert_unicode_to_string_list(self):
        u_list = [u'first string', u'second string']
        result = util.convert_unicode_to_string(u_list)
        assert_equal(result, ["first string", "second string"])

    def test_convert_unicode_to_string_dict(self):
        u_dict = {u'key': u'value'}
        result = util.convert_unicode_to_string(u_dict)
        assert_equal(result, {"key": "value"})

    def test_convert_unicode_to_string_mixed_recursion(self):
        u_object = {u'string': u'test string',
                    u'list': [u'unicode string', "normal string"]
                    }
        result = util.convert_unicode_to_string(u_object)
        expected_result = {
                            'string': 'test string',
                            'list': ['unicode string', "normal string"]
                          }
        assert_equal(result, expected_result)