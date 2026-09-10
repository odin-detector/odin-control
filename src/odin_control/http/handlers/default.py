"""Default static-content request handler for odin-control.

This module implements the default handler used to serve static files from the root URL route. This
is a thin wrapper around the Tornado StaticFileHandler, allowing for integration with the handler
mixin to correctly implement CORS and server header behaviour.

Tim Nicholls, STFC Detector Systems Software Group
"""

from tornado.web import StaticFileHandler

from odin_control.http.handlers.mixin import HandlerMixin


class DefaultHandler(HandlerMixin, StaticFileHandler):
    """Default URL handler for static file content."""

    pass
