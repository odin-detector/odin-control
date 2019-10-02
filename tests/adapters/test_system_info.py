""" Unit tests for the ODIN SystemInfo adapter.

Tim Nicholls, STFC Application Engineering Group.
"""

import sys

import pytest

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock
else:                         # pragma: no cover
    from mock import Mock

from odin.adapters.system_info import SystemInfoAdapter, SystemInfo

@pytest.fixture(scope="class")
def test_system_info():
    """Fixture for use in testing the SystemInfo class."""
    test_system_info = SystemInfo()
    yield test_system_info


class TestSystemInfo():
    """Test cases for the SystemInfo class."""

    def test_system_info_single_instance(self, test_system_info):
        """Test that the SystemInfo class exhibits singleton behaviour."""
        new_instance = SystemInfo()
        assert test_system_info == new_instance

    def test_system_info_get(self, test_system_info):
        """Test the calling the GET method of system info returns a dict."""
        result = test_system_info.get('')
        assert type(result) is dict


class SystemInfoAdapterTestFixture():
    """Container class used in fixtures for testing SystemInfoAdapter."""
    def __init__(self):

        self.adapter = SystemInfoAdapter()
        self.path = ''
        self.request = Mock()
        self.request.headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}


@pytest.fixture(scope="class")
def test_sysinfo_adapter():
    """Fixture used in SystemInfoAdapter test cases."""
    test_sysinfo_adapter = SystemInfoAdapterTestFixture()
    yield test_sysinfo_adapter


class TestSystemInfoAdapter():
    """Test cases for the SystemInfoAdapter class.
    """

    def test_adapter_get(self, test_sysinfo_adapter):
        """Test that a GET call to the adapter returns the appropriate response."""
        response = test_sysinfo_adapter.adapter.get(
            test_sysinfo_adapter.path, test_sysinfo_adapter.request)

        assert type(response.data) == dict
        assert 'odin_version' in response.data
        assert response.status_code == 200

    def test_adapter_get_bad_path(self, test_sysinfo_adapter):
        """Test that a GET call to the adapter with a bad path returns an appropriate error."""
        bad_path = '/bad/path'
        expected_response = {'error': 'Invalid path: {}'.format(bad_path)}

        response = test_sysinfo_adapter.adapter.get(bad_path, test_sysinfo_adapter.request)

        assert response.data == expected_response
        assert response.status_code == 400

    def test_adapter_put(self, test_sysinfo_adapter):
        """Test that a PUT call to the adapter returns the appropriate response."""
        expected_response = {
            'response': 'SystemInfoAdapter: PUT on path {}'.format(test_sysinfo_adapter.path)
        }

        response = test_sysinfo_adapter.adapter.put(
            test_sysinfo_adapter.path, test_sysinfo_adapter.request)

        assert response.data == expected_response
        assert response.status_code == 200

    def test_adapter_delete(self, test_sysinfo_adapter):
        """Test that a DELETE call to the adapter returns an appropriate response."""
        response = test_sysinfo_adapter.adapter.delete(
            test_sysinfo_adapter.path, test_sysinfo_adapter.request)

        assert response.data == 'SystemInfoAdapter: DELETE on path {}'.format(
            test_sysinfo_adapter.path)
        assert response.status_code == 200

    def test_adapter_put_bad_content_type(self, test_sysinfo_adapter):
        """Test that PUT call with a bad content type returns the appropriate error."""
        bad_request = Mock()
        bad_request.headers = {'Content-Type': 'text/plain'}

        response = test_sysinfo_adapter.adapter.put(test_sysinfo_adapter.path, bad_request)

        assert response.data == 'Request content type (text/plain) not supported'
        assert response.status_code == 415

    def test_adapter_put_bad_accept_type(self, test_sysinfo_adapter):
        """Test that a PUT call with a bad accept type returns the appropriate error."""
        bad_request = Mock()
        bad_request.headers = {'Accept': 'text/plain'}

        response = test_sysinfo_adapter.adapter.put(test_sysinfo_adapter.path, bad_request)

        assert response.data == 'Requested content types not supported'
        assert response.status_code == 406


class SystemInfoAdapterMetadataTestFixture():
    """Container class used in fixtures for testing SystemInfoAdapter metadata."""

    def __init__(self):

        self.adapter = SystemInfoAdapter()
        self.path = ''
        self.request = Mock()
        self.request.headers = {
           'Accept': 'application/json;metadata=True', 
           'Content-Type': 'application/json' 
        }
        self.response = self.adapter.get(self.path, self.request)
        self.top_level_metadata = ('name', 'description')


@pytest.fixture(scope="class")
def test_sysinfo_metadata():
    """Fixture used in SystemInfoAdapter metadata test cases."""
    test_sysinfo_adapter = SystemInfoAdapterMetadataTestFixture()
    yield test_sysinfo_adapter


class TestSystemInfoAdapterMetadata():
    """Test cases for SystemInfoAdapter metadata behaviour."""

    def test_adapter_has_toplevel_metadata(self, test_sysinfo_metadata):
        """Test that the adapter has the appropriate top-level metadata."""
        for field in test_sysinfo_metadata.top_level_metadata:
            assert field in test_sysinfo_metadata.response.data

    def test_adapter_params_have_toplevel_metadata(self, test_sysinfo_metadata):
        """Test that all parameters exposed by the adapter also have top-level metadata."""
        for (param, val) in test_sysinfo_metadata.response.data.items():
            if param not in test_sysinfo_metadata.top_level_metadata:
                for field in test_sysinfo_metadata.top_level_metadata:
                    assert field in val

    def test_adapter_params_have_metadata(self, test_sysinfo_metadata):
        """
        Test that all parameters exposed by the adapter have value, type and writeable 
        metadata fields.
        """
        for (param, val) in test_sysinfo_metadata.response.data.items():
            if param not in test_sysinfo_metadata.top_level_metadata and param != 'platform':
                assert 'value' in val
                assert 'type' in val
                assert 'writeable' in val

    def test_subtree_has_metadata(self, test_sysinfo_metadata):
        """
        Test that the platform subtree within the adapter parameters also has the appropriate
        metadata.
        """
        subtree = test_sysinfo_metadata.response.data['platform']
        for field in test_sysinfo_metadata.top_level_metadata:
            assert field in subtree

        for (param, val) in subtree.items():
            if param not in test_sysinfo_metadata.top_level_metadata:
                assert 'value' in val
                assert 'type' in val
                assert 'writeable' in val