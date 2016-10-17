import sys

from nose.tools import *

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock
else:                         # pragma: no cover
    from mock import Mock

from odin.adapters.system_info import SystemInfoAdapter, SystemInfo

class TestSystemInfo():

    @classmethod
    def setup_class(cls):

        cls.system_info = SystemInfo()

    def test_system_info_single_instance(self):

        new_instance = SystemInfo()
        assert_equal(self.system_info, new_instance)

    def test_system_info_get(self):

        result = self.system_info.get('')
        assert_equal(type(result), dict)

class TestSystemInfoAdapter():

    @classmethod
    def setup_class(cls):

        cls.adapter = SystemInfoAdapter()
        cls.path = ''
        cls.request = Mock()
        cls.request.headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    def test_adapter_get(self):
        response = self.adapter.get(self.path, self.request)

        assert_equal(type(response.data), dict)
        assert_true('odin_version' in response.data)
        assert_equal(response.status_code, 200)

    def test_adapter_get_bad_path(self):
        bad_path = '/bad/path'
        expected_response = {'error': 'The path {} is invalid'.format(bad_path)}
        response = self.adapter.get(bad_path, self.request)
        assert_equal(response.data, expected_response)
        assert_equal(response.status_code, 400)

    def test_adapter_put(self):

        expected_response = {'response': 'SystemInfoAdapter: PUT on path {}'.format(self.path)}
        response = self.adapter.put(self.path, self.request)
        assert_equal(response.data, expected_response)
        assert_equal(response.status_code, 200)

    def test_adapter_delete(self):
        response = self.adapter.delete(self.path, self.request)
        assert_equal(response.data, 'SystemInfoAdapter: DELETE on path {}'.format(self.path))
        assert_equal(response.status_code, 200)

    def test_adapter_put_bad_content_type(self):
        bad_request = Mock()
        bad_request.headers = {'Content-Type': 'text/plain'}
        response = self.adapter.put(self.path, bad_request)
        assert_equal(response.data, 'Request content type (text/plain) not supported')
        assert_equal(response.status_code, 415)

    def test_adapter_put_bad_accept_type(self):
        bad_request = Mock()
        bad_request.headers = {'Accept': 'text/plain'}
        response = self.adapter.put(self.path, bad_request)
        assert_equal(response.data, 'Requested content types not supported')
        assert_equal(response.status_code, 406)
