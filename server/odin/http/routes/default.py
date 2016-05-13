"""Default handler for ODIN server.

This module provides a default URL ('/') handler for the ODIN server, redirecting the client
to the static page handler.

Tim Nicholls, STFC Application Engineering
"""
import tornado.web
from odin.http.routes.route import Route


class DefaultHandler(tornado.web.RequestHandler):
    """Default URL handler for ODIN."""

    def get(self):
        """Handle HTTP GET requests."""
        self.redirect("/static/index.html")


class DefaultRoute(Route):
    """Default URL Route for the ODIN server."""

    def __init__(self):
        """Initialise the default route, adding a handler."""
        self.add_handler((r"/", DefaultHandler))
