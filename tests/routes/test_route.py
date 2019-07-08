#from nose.tools import *

from odin.http.routes.route import Route

class DummyHandler(object):
    pass

class TestRoute():
    """Class for testing the Route object."""
    def test_empty_route(self):
        """Test that an empty route has no handlers."""
        empty_route = Route()

        assert len(empty_route.get_handlers()) == 0

    def test_simple_route(self):
        """Test that a simmple Route with one or more handlers works correctly."""
        url_spec1= (r"/", DummyHandler)
        url_spec2 = (r"/", None)

        simple_route = Route()
        simple_route.add_handler(url_spec1)

        assert len(simple_route.get_handlers()) ==  1
        assert simple_route.get_handlers()[0] == url_spec1

        simple_route.add_handler(url_spec2)

        assert len(simple_route.get_handlers()) == 2

        for (spec, handler) in zip([url_spec1, url_spec2], simple_route.get_handlers()):
            assert spec == handler
