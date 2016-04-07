from nose.tools import *

from odin.http.routes.api import ApiDispatcher

class TestApiDispatcher():

    @classmethod
    def setup_class(cls):
        cls.dispatcher = ApiDispatcher()

    def test_register_adapter(self):

        self.dispatcher.register_adapter("dummy", "odin.adapters.dummy.DummyAdapter")

    def test_register_adapter_badmodule(self):

        with assert_raises(ImportError) as cm:
            self.dispatcher.register_adapter("dummy", "odin.adapters.dummyd.DummyAdapter")
        assert_equal(str(cm.exception), "No module named dummyd")

    def test_register_adapter_badclass(self):

        with assert_raises(AttributeError) as cm:
            self.dispatcher.register_adapter("dummy", "odin.adapters.dummy.BadAdapter")
        assert_equal(str(cm.exception), "'module' object has no attribute 'BadAdapter'")
