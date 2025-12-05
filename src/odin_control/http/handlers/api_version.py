"""API version handler module for odin-control.

This module implements the API version handler. It allows clients to query the supported API version
through HTTP GET requests, returning the version information as JSON.

Tim Nicholls, STFC Detector Systems Software Group.
"""
import json

from tornado.web import RequestHandler


class ApiVersionHandler(RequestHandler):
    """API version handler to allow client to resolve supported version.

    This request handler implements the GET verb to allow a call to the appropriate URI to return
    the supported API version as JSON.
    """

    def initialize(self, route):
        """Initialise the ApiVersionHandler.

        :param route: ApiRoute object calling the handler (allows API version to be resolved)
        """
        self.route = route

    def get(self):
        """Handle API version GET requests."""
        accept_types = self.request.headers.get('Accept', 'application/json').split(',')
        if "*/*" not in accept_types and 'application/json' not in accept_types:
            self.set_status(406)
            self.write('Requested content types not supported')
            return

        self.write(json.dumps({'version': self.route.api_version}))
