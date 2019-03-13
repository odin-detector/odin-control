import sys

from odin.adapters.dummy import DummyAdapter, IacDummyAdapter
from odin.adapters.adapter import (ApiAdapter, ApiAdapterRequest,
                                   ApiAdapterResponse, request_types, response_types)

from nose.tools import *

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock
else:                         # pragma: no cover
    from mock import Mock


class TestDummyAdapter():

    @classmethod
    def setup_class(cls):

        cls.adapter = DummyAdapter()
        cls.path = '/dummy/path'
        cls.request = Mock()
        cls.request.headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    def test_adapter_get(self):
        expected_response = {'response': 'DummyAdapter: GET on path {}'.format(self.path)}
        response = self.adapter.get(self.path, self.request)
        assert_equal(response.data, expected_response)
        assert_equal(response.status_code, 200)

    def test_adapter_put(self):

        expected_response = {'response': 'DummyAdapter: PUT on path {}'.format(self.path)}
        response = self.adapter.put(self.path, self.request)
        assert_equal(response.data, expected_response)
        assert_equal(response.status_code, 200)

    def test_adapter_delete(self):
        response = self.adapter.delete(self.path, self.request)
        assert_equal(response.data, 'DummyAdapter: DELETE on path {}'.format(self.path))
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

    def test_adapter_cleanup(self):
        self.adapter.background_task_counter = 1000
        self.adapter.cleanup()
        assert_equal(self.adapter.background_task_counter, 0)


class FakeAdapter(ApiAdapter):

    def get(self, path, request):
        response = "GET method not implemented by {}".format(self.name)
        return ApiAdapterResponse(response, status_code=400)

    @request_types('application/json', 'application/vnd.odin-native')
    @response_types('application/json', default='application/json')
    def put(self, path, request):
        response = "PUT received by {}, data: {}".format(self.name, request.body)
        return ApiAdapterResponse(response, status_code=400)


class TestIacDummyAdapter():

    @classmethod
    def setup_class(cls):
        fake_adapter = FakeAdapter()
        cls.adapters = {"fake_adapter": fake_adapter}
        cls.adapters_no_add = {"fake_adapter": fake_adapter}

    def setup(self):
        self.adapter = IacDummyAdapter()
        self.adapters["iac_adapter"] = self.adapter
        self.adapter.initialize(self.adapters)

    def test_iac_adapter_initialize(self):
        assert_equal(self.adapter.adapters, self.adapters_no_add)

    def test_iac_adapter_get(self):
        path = ""
        request = ApiAdapterRequest(None)
        response = self.adapter.get(path, request)
        assert_equal(response.data,
                     {"fake_adapter": "GET method not implemented by FakeAdapter"})

    def test_iac_adapter_put(self):
        path = ""
        data = {"test": "value"}
        request = ApiAdapterRequest(data, content_type="application/json")
        response = self.adapter.put(path, request)
        assert_equal(response.data,
                     {"fake_adapter": "PUT received by FakeAdapter, data: {}".format(data)})
