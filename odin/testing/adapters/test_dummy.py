import sys

import pytest

from odin.adapters.dummy import DummyAdapter, IacDummyAdapter
from odin.adapters.adapter import (ApiAdapter, ApiAdapterRequest,
                                   ApiAdapterResponse, request_types, response_types)

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock
else:                         # pragma: no cover
    from mock import Mock


class DummyAdapterTestFixture(object):
    """Container class used in fixtures for testing the DummyAdapter."""

    def __init__(self):

        self.adapter = DummyAdapter(background_task_enable=True)
        self.path = '/dummy/path'
        self.request = Mock()
        self.request.headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

@pytest.fixture(scope="class")
def test_dummy_adapter():
    """Simple test fixture for testing the dummy adapter."""
    test_dummy_adapter = DummyAdapterTestFixture()
    yield test_dummy_adapter

class TestDummyAdapter():

    def test_adapter_get(self, test_dummy_adapter):
        """Test that a call to the GET method of the dummy adapter returns the correct response."""
        expected_response = {
            'response': 'DummyAdapter: GET on path {}'.format(test_dummy_adapter.path)
            }
        response = test_dummy_adapter.adapter.get(test_dummy_adapter.path, 
            test_dummy_adapter.request)
        assert response.data == expected_response
        assert response.status_code == 200

    def test_adapter_put(self, test_dummy_adapter):
        """Test that a call to the PUT method of the dummy adapter returns the correct response."""
        expected_response = {
            'response': 'DummyAdapter: PUT on path {}'.format(test_dummy_adapter.path)
            }
        response = test_dummy_adapter.adapter.put(test_dummy_adapter.path,
            test_dummy_adapter.request)
        assert response.data == expected_response
        assert response.status_code == 200

    def test_adapter_delete(self, test_dummy_adapter):
        """Test that a call to the DELETE method of the dummy adapter returns the correct response."""
        response = test_dummy_adapter.adapter.delete(test_dummy_adapter.path, 
            test_dummy_adapter.request)
        assert response.data == 'DummyAdapter: DELETE on path {}'.format(test_dummy_adapter.path)
        assert response.status_code == 200

    def test_adapter_put_bad_content_type(self, test_dummy_adapter):
        """
        Test that a call to the dummy adapter with an incorrect content type generates the
        appropriate error response.
        """
        bad_request = Mock()
        bad_request.headers = {'Content-Type': 'text/plain'}
        response = test_dummy_adapter.adapter.put(test_dummy_adapter.path, bad_request)
        assert response.data == 'Request content type (text/plain) not supported'
        assert response.status_code == 415

    def test_adapter_put_bad_accept_type(self, test_dummy_adapter):
        """
        Test that a call to the dummy adapter with an incorrect accept type generates the
        appropriate error response.
        """
        bad_request = Mock()
        bad_request.headers = {'Accept': 'text/plain'}
        response = test_dummy_adapter.adapter.put(test_dummy_adapter.path, bad_request)
        assert response.data == 'Requested content types not supported'
        assert response.status_code == 406

    def test_adapter_cleanup(self, test_dummy_adapter):
        """
        Test that a call the dummy adapter cleanup method cleans up correctly.
        """
        test_dummy_adapter.adapter.background_task_counter = 1000
        test_dummy_adapter.adapter.cleanup()
        assert test_dummy_adapter.adapter.background_task_counter == 0


class FakeAdapter(ApiAdapter):
    """Fake adapter class used for testing with the dummy IAC adapter."""
    def get(self, path, request):
        response = "GET method not implemented by {}".format(self.name)
        return ApiAdapterResponse(response, status_code=400)

    @request_types('application/json', 'application/vnd.odin-native')
    @response_types('application/json', default='application/json')
    def put(self, path, request):
        response = "PUT received by {}, data: {}".format(self.name, request.body)
        return ApiAdapterResponse(response, status_code=400)


class IacDummyAdapterTestFixture():
    """Container class used in fixtures for testing the IAC dummy adapter."""

    def __init__(self):

        # Set up the fake adapter
        self.fake_adapter = FakeAdapter()
        self.adapters = {"fake_adapter": self.fake_adapter}
        self.adapters_no_add = {"fake_adapter": self.fake_adapter}

        # Set up and initialize the IacDummy adapter, which will then access the fake adapter.""""
        self.iac_adapter = IacDummyAdapter()
        self.adapters["iac_adapter"] = self.iac_adapter
        self.iac_adapter.initialize(self.adapters)

@pytest.fixture(scope="class")
def test_iac_dummy_adapter():
    ###Test fixture used for testing dummy IAC adapter."""
    test_iac_dummy_adapter = IacDummyAdapterTestFixture()
    yield test_iac_dummy_adapter

class TestIacDummyAdapter():

    def test_iac_adapter_initialize(self, test_iac_dummy_adapter):
        """Test that the list of adapters held by the IAC dummmy doesn't contain itself."""
        assert test_iac_dummy_adapter.iac_adapter.adapters == test_iac_dummy_adapter.adapters_no_add

    def test_iac_adapter_get(self, test_iac_dummy_adapter):
        """
        Test that the GET method of the IAC dummy adapter returns the output of the fake
        adapter's GET method.
        """
        path = ""
        request = ApiAdapterRequest(None)
        response = test_iac_dummy_adapter.iac_adapter.get(path, request)
        assert response.data == {"fake_adapter": "GET method not implemented by FakeAdapter"}

    def test_iac_adapter_put(self, test_iac_dummy_adapter):
        """
        Test that the PUT method of the IAC dummy adapter returns the output of the fake
        adapter's PUT method.
        """
        path = ""
        data = {"test": "value"}
        request = ApiAdapterRequest(data, content_type="application/json")
        response = test_iac_dummy_adapter.iac_adapter.put(path, request)
        assert response.data == {
            "fake_adapter": "PUT received by FakeAdapter, data: {}".format(data)
        }
