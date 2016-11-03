"""Default handler for ODIN server.

This module provides a default URL ('/') handler for the ODIN server, redirecting the client
to the static page handler.

Tim Nicholls, STFC Application Engineering
"""
import logging
import os
import tornado.web
from odin.http.routes.route import Route


class DefaultHandler(tornado.web.StaticFileHandler):
    """Default URL handler for ODIN.

    This is a simple subclass of the StaticFileHandler to serve static
    files for the default route, i.e. to give a simple top-level
    view aimed at broswers.
    """

    pass


class DefaultRoute(Route):
    """Default URL Route for the ODIN server."""

    def __init__(self, path, default_filename='index.html'):
        """Initialise the default route, adding a handler.

        This route provides the default view for the ODIN server, rendering
        static content suitable for use in a browser.

        :param path: path to serve static content from
        :param default_filename: default filename serve for directory requests
        """
        if not os.path.isdir(path):
            logging.warning('Default handler static path does not exist: %s', path)
        else:
            logging.debug('Static path for default handler is %s', path)

        # Create argument dictionary to initialise default handler
        self.default_handler_args = {
            'path': path,
            'default_filename': default_filename,
        }
        self.add_handler((r"/(.*)", DefaultHandler, self.default_handler_args))
