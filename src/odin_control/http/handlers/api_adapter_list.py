"""API adapter list handler module for odin-control.

This module implements the API adapter list handler. It allows clients to query the list of loaded
API adapters through HTTP GET requests, returning the adapter information as JSON.

Tim Nicholls, STFC Detector Systems Software Group.
"""
from tornado.web import RequestHandler


class ApiAdapterListHandler(RequestHandler):
    """API adapter list handler to return a list of loaded adapters.

    This request hander implements the GET verb to allow a call to the appropriate URI to return
    a JSON-encoded list of adapters loaded by the server.
    """

    def initialize(self, route):
        """Initialize the API adapter list handler.

        :param route: ApiRoute object calling the handler (allows adapters to be resolved)
        """
        self.route = route

    def get(self, version=None):
        """Handle API adapter list GET requests.

        This handler returns a JSON-encoded list of adapters loaded into the server.

        :param version: API version (or None if versioning not enabled)
        """
        # Validate the API version explicity - can't use the validate_api_request decorator here
        if version != self.route.api_version:
            self.set_status(400)
            self.write("API version {} is not supported".format(version))
            return

        # Validate the accept type requested is appropriate
        accept_types = self.request.headers.get('Accept', 'application/json').split(',')
        if '*/*' not in accept_types and 'application/json' not in accept_types:
            self.set_status(406)
            self.write('Request content types not supported')
            return

        # Return a list of loaded adapters
        self.write({'adapters': list(self.route.adapters)})
