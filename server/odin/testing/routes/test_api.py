from nose.tools import *

from odin.http.routes.api import ApiRoute, ApiError

class TestApiAdapters():

    @classmethod
    def setup_class(cls):
        cls.api_route = ApiRoute()

    def test_register_adapter(self):

        self.api_route.register_adapter("dummy", "odin.adapters.dummy.DummyAdapter")

    def test_register_adapter_badmodule(self):

        with assert_raises(ApiError) as cm:
            self.api_route.register_adapter("dummy", "odin.adapters.dummyd.DummyAdapter", fail_ok=False)
        assert_equal(str(cm.exception), "No module named dummyd")

    def test_register_adapter_badclass(self):

        with assert_raises(ApiError) as cm:
            self.api_route.register_adapter("dummy", "odin.adapters.dummy.BadAdapter", fail_ok=False)
        assert_equal(str(cm.exception), "'module' object has no attribute 'BadAdapter'")


class TestApiRoute():

    # @classmethod
    # def setup_class(cls):
    #     cls.api_route = ApiRoute()

    def test_api_route_has_handlers(self):

        api_route = ApiRoute()
        assert(len(api_route.get_handlers()) > 0)
