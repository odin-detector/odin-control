from nose.tools import *

from odin.adapters.dummy import DummyAdapter

class TestDummyAdapter():

    @classmethod
    def setup_class(cls):

        cls.adapter = DummyAdapter()
        cls.path = '/dummy/path'

    def test_adapter_get(self):
        (response, code) = self.adapter.get(self.path)
        assert_equal(response, 'DummyAdapter: GET on path {}'.format(self.path))
        assert_equal(code, 200)


    def test_adapter_put(self):
        (response, code) = self.adapter.put(self.path)
        assert_equal(response, 'DummyAdapter: PUT on path {}'.format(self.path))
        assert_equal(code, 200)


    def test_adapter_delete(self):
        (response, code) = self.adapter.delete(self.path)
        assert_equal(response, 'DummyAdapter: DELETE on path {}'.format(self.path))
        assert_equal(code, 200)
