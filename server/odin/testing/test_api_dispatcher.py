from nose.tools import *

from odin.http.routes.api import ApiDispatcher, ApiError

class TestApiDispatcher():

    @classmethod
    def setup_class(cls):
        cls.dispatcher = ApiDispatcher()

    def test_register_adapter(self):

        self.dispatcher.register_adapter("dummy", "odin.adapters.dummy.DummyAdapter")

    def test_register_adapter_badmodule(self):

        with assert_raises(ApiError) as cm:
            self.dispatcher.register_adapter("dummy", "odin.adapters.dummyd.DummyAdapter", fail_ok=False)
        assert_equal(str(cm.exception), "No module named dummyd")

    def test_register_adapter_badclass(self):

        with assert_raises(ApiError) as cm:
            self.dispatcher.register_adapter("dummy", "odin.adapters.dummy.BadAdapter", fail_ok=False)
        assert_equal(str(cm.exception), "'module' object has no attribute 'BadAdapter'")
