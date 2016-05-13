"""odin.http.server - ODIN HTTP Server class.

This module provides the core HTTP server class used in ODIN, which handles all client requests,
handing off API requests to the appropriate API route and adapter plugins, and defining the
default route used to serve static content.

Tim Nicholls, STFC Application Engineering
"""
import os
import logging

import tornado.gen
import tornado.web
import tornado.ioloop

from odin.http.routes.api import ApiRoute
from odin.http.routes.default import DefaultRoute


class HttpServer(object):
    """HTPP server class."""

    def __init__(self, debug_mode=False, adapters=None):
        """Initialise the HttpServer object.

        :param debug_mode: Set True to enable Tornado debug mode
        :param adapters: list of adapters to register with API route
        """
        settings = {
            "static_path": os.path.abspath(os.path.join(os.path.dirname(__file__), "../static")),
            "debug": debug_mode,
        }

        logging.debug("static_path is %s", settings['static_path'])

        # Create an API route
        api_route = ApiRoute()

        # Register adapters with the API route and get handlers
        for adapter in adapters:
            api_route.register_adapter(adapters[adapter])

        handlers = api_route.get_handlers()

        # Craete a default route for static content and get handlers
        default_route = DefaultRoute()
        handlers += default_route.get_handlers()

        # Create the Tornado web application for these handlers
        self.application = tornado.web.Application(handlers, **settings)

    def listen(self, port, host=''):
        """Listen for HTTP client requests.

        :param port: port to listen on
        :param host: host address to listen on
        """
        self.application.listen(port, host)
