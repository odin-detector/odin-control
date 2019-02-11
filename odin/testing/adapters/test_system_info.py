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
        expected_response = {'error': 'Invalid path: {}'.format(bad_path)}
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


class TestSystemInfoAdapterMetadata():

    @classmethod
    def setup_class(cls):

        cls.adapter = SystemInfoAdapter()
        cls.path = ''
        cls.request = Mock()
        cls.request.headers = {
           'Accept': 'application/json;metadata=True', 
           'Content-Type': 'application/json' 
        }
        cls.response = cls.adapter.get(cls.path, cls.request)
        cls.top_level_metadata = ('name', 'description')

    def test_adapter_has_toplevel_metadata(self):

        for field in self.top_level_metadata:
            assert_true(field in self.response.data)

    def test_adapter_params_have_toplevel_metadata(self):

        for (param, val) in self.response.data.items():
            if param not in self.top_level_metadata:
                for field in self.top_level_metadata:
                    assert_true(field in val)

    def test_adapter_params_have_metadata(self):

        for (param, val) in self.response.data.items():
            if param not in self.top_level_metadata and param != 'platform':
                assert_true('value' in val)
                assert_true('type' in val)
                assert_true('writeable' in val)

    def test_subtree_has_metadata(self):

        subtree = self.response.data['platform']
        for field in self.top_level_metadata:
            assert_true(field in subtree)

        for (param, val) in subtree.items():
            if param not in self.top_level_metadata:
                assert_true('value' in val)
                assert_true('type' in val)
                assert_true('writeable' in val)