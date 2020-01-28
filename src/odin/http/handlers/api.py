"""Synchronous API handler for the ODIN server.

This module implements the synchronous API handler used by the ODIN server to pass
API calls to synchronous adapters.

Tim Nicholls, STFC Detector Systems Software Group.
"""

from odin.http.handlers.base import BaseApiHandler, validate_api_request, API_VERSION


class ApiHandler(BaseApiHandler):
    """Class for handling synchrounous API requests.

    This class handles synchronous API requests, that is when the ODIN server is being
    used with Tornado and python versions incompatible with native async behaviour.
    """

    @validate_api_request(API_VERSION)
    def get(self, subsystem, path=''):
        """Handle an API GET request.

        :param subsystem: subsystem element of URI, defining adapter to be called
        :param path: remaining URI path to be passed to adapter method
        """
        response = self.route.adapter(subsystem).get(path, self.request)
        self.respond(response)

    @validate_api_request(API_VERSION)
    def put(self, subsystem, path=''):
        """Handle an API PUT request.

        :param subsystem: subsystem element of URI, defining adapter to be called
        :param path: remaining URI path to be passed to adapter method
        """
        response = self.route.adapter(subsystem).put(path, self.request)
        self.respond(response)

    @validate_api_request(API_VERSION)
    def delete(self, subsystem, path=''):
        """Handle an API DELETE request.

        :param subsystem: subsystem element of URI, defining adapter to be called
        :param path: remaining URI path to be passed to adapter method
        """
        response = self.route.adapter(subsystem).delete(path, self.request)
        self.respond(response)
