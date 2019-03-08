from nose.tools import assert_equal, assert_true
from odin.adapters.iac_dummy_target import IacDummyTargetAdapter
from odin.adapters.adapter import ApiAdapterRequest


class TestIacDummyTargetAdapter():

    def setup(self):
        self.kwargs = {"Test": 1}
        self.adapter = IacDummyTargetAdapter(**self.kwargs)

    def test_target_adapter_init(self):
        assert_equal(self.adapter.param_tree.get(""), self.kwargs)

    def test_target_adapter_get(self):
        request = ApiAdapterRequest(None)
        path = ""
        response = self.adapter.get(path, request)

        assert_equal(response.data, self.kwargs)
        assert_equal(response.status_code, 200)

    def test_target_adapter_get_invalid_path(self):
        request = ApiAdapterRequest(None)
        path = "Invalid/notcorrect"

        response = self.adapter.get(path, request)

        assert_true("error" in response.data)
        assert_equal(response.status_code, 400)

    def test_target_adapter_put(self):
        data = {"Test": 1}
        request = ApiAdapterRequest(data)
        path = ""

        response = self.adapter.put(path, request)
        assert_equal(response.data["data"], data)
        assert_true("response" in response.data)
