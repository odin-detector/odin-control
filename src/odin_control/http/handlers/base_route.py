"""Generic route handler base class for odin-control.

This module implements the BaseRouteHandler class on which API handlers are based. This is a wrapper
around the Tornado RequestHandler, adding the handler mixin to provide CORS and Server header
behaviour.

Tim Nicholls, STFC Detector Systems Software Group
"""

from typing import Any

from tornado.web import RequestHandler

from odin_control.http.handlers.mixin import HandlerMixin


class BaseRouteHandler(HandlerMixin, RequestHandler):
    """Base route handler class with CORS and server-header support."""

    def __init__(self, *args, **kwargs):
        """Construct the BaseRouteHandler object."""
        self.route: Any = None
        super().__init__(*args, **kwargs)

    def initialize(self, route, **kwargs):
        """Initialise the BaseRouteHandler object with route and optional kwargs."""
        self.route = route
        super().initialize(**kwargs)
