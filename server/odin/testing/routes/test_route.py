from nose.tools import *

from odin.http.routes.route import Route

class DummyHandler(object):
    pass

class TestRoute():

    def test_empty_route(self):

        empty_route = Route()

        assert_equal(len(empty_route.get_handlers()), 0)

    def test_simple_route(self):

        url_spec1= (r"/", DummyHandler)
        url_spec2 = (r"/", None)

        simple_route = Route()
        simple_route.add_handler(url_spec1)

        assert_equal(len(simple_route.get_handlers()), 1)
        assert_equal(simple_route.get_handlers()[0], url_spec1)

        simple_route.add_handler(url_spec2)

        assert_equal(len(simple_route.get_handlers()), 2)

        for (spec, handler) in zip([url_spec1, url_spec2], simple_route.get_handlers()):
            assert_equal(spec, handler)
