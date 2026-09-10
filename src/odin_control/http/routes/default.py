"""Default handler for ODIN server.

This module provides a default URL ('/') handler for the ODIN server, redirecting the client
to the static page handler.

Tim Nicholls, STFC Application Engineering
"""
import logging
import os

from odin_control.http.handlers.default import DefaultHandler
from odin_control.http.routes.route import Route


class DefaultRoute(Route):
    """Default URL Route for the ODIN server."""

    def __init__(self, path, default_filename='index.html', enable_cors=False, cors_origin='*'):
        """Initialise the default route, adding a handler.

        This route provides the default view for the ODIN server, rendering
        static content suitable for use in a browser.

        :param path: path to serve static content from
        :param default_filename: default filename serve for directory requests
        :param enable_cors: flag to enable CORS request support
        :param cors_origin: CORS allowed origins
        """
        if not os.path.isdir(path):
            logging.warning('Default handler static path does not exist: %s', path)
        else:
            logging.debug('Static path for default handler is %s', path)

        # Create argument dictionary to initialise default handler
        self.default_handler_args = {
            'path': path,
            'default_filename': default_filename,
            'enable_cors': enable_cors,
            'cors_origin': cors_origin,
        }
        self.add_handler((r"/(.*)", DefaultHandler, self.default_handler_args))
