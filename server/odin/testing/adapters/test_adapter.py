from nose.tools import *

from odin.adapters.adapter import ApiAdapter

class TestApiAdapter():

    @classmethod
    def setup_class(cls):

        cls.adapter = ApiAdapter()
        cls.path = '/api/path'

    def test_adapter_get(self):
        (response, code) = self.adapter.get(self.path)
        assert_equal(response, 'GET method not implemented by ApiAdapter')
        assert_equal(code, 400)


    def test_adapter_put(self):
        (response, code) = self.adapter.put(self.path)
        assert_equal(response, 'PUT method not implemented by ApiAdapter')
        assert_equal(code, 400)


    def test_adapter_delete(self):
        (response, code) = self.adapter.delete(self.path)
        assert_equal(response, 'DELETE method not implemented by ApiAdapter')
        assert_equal(code, 400)
