from nose.tools import *

from odin.http.routes.api import ApiRoute, ApiError

class TestApiAdapters():

    @classmethod
    def setup_class(cls):
        cls.api_route = ApiRoute()

    def test_register_adapter(self):

        self.api_route.register_adapter('dummy', 'odin.adapters.dummy.DummyAdapter')

    def test_register_adapter_badmodule(self):

        with assert_raises_regexp(ApiError, 'No module named'):
            self.api_route.register_adapter('dummy', 'odin.adapters.dummyd.DummyAdapter', fail_ok=False)

    def test_register_adapter_badclass(self):

        with assert_raises_regexp(ApiError, 'has no attribute \'BadAdapter\''):
            self.api_route.register_adapter('dummy', 'odin.adapters.dummy.BadAdapter', fail_ok=False)


class TestApiRoute():

    # @classmethod
    # def setup_class(cls):
    #     cls.api_route = ApiRoute()

    def test_api_route_has_handlers(self):

        api_route = ApiRoute()
        assert(len(api_route.get_handlers()) > 0)
