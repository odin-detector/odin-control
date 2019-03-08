from nose.tools import assert_equal
from odin.adapters.iac_dummy import IacDummyAdapter
from odin.adapters.adapter import ApiAdapter, ApiAdapterRequest, \
                                ApiAdapterResponse, request_types, response_types


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
