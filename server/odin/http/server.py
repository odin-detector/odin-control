import os
import time
import json
import logging

import tornado.gen
import tornado.web
import tornado.ioloop

from odin.http.routes.api import ApiRoute
from odin.http.routes.default import DefaultRoute

class HttpServer(object):

    def __init__(self, debug_mode=False):

        settings = {
            "static_path": os.path.abspath(os.path.join(os.path.dirname(__file__), "../static")),
            "debug" : debug_mode,
            }

        logging.debug("static_path is {}".format(settings['static_path']))

        routes = []

        api_route = ApiRoute()
        api_route.register_adapter("dummy", "odin.adapters.dummy.DummyAdapter")
        routes = api_route.add_to(routes)

        default_route = DefaultRoute()
        routes = default_route.add_to(routes)
        print routes

        self.application = tornado.web.Application(routes, **settings)

#        self.application.add_handlers(r"/api/(.*?)/(.*?)/(.*)", ApiHandler)
#        ApiRoute().add(self.application)
#        self.application.add_handlers(*DefaultRoute)

    def listen(self, port, host=''):

        self.application.listen(port, host)
