import os
import time
import json
import logging

import tornado.gen
import tornado.web
import tornado.ioloop

from odin.http.routes.api import ApiDispatcher, ApiHandler, ApiRoute
from odin.http.routes.default import DefaultRoute

class HttpServer(object):

    def __init__(self, debug_mode=False):

        settings = {
            "static_path": os.path.abspath(os.path.join(os.path.dirname(__file__), "../static")),
            "debug" : debug_mode,
            }

        self.application = tornado.web.Application([
            ApiRoute,
            DefaultRoute,
        ], **settings)

        dispatcher = ApiDispatcher()
        dispatcher.register_adapter("dummy", "odin.adapters.dummy.DummyAdapter")
        dispatcher.register_adapter("dummy2", "ond.one.TWO")
        
    def listen(self, port, host=''):

        self.application.listen(port, host)
