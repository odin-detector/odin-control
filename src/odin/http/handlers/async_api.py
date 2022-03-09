"""Asynchronous API handler for the ODIN server.

This module implements the asynchronous API handler used by the ODIN server to pass
API calls to asynchronous adapters.

Tim Nicholls, STFC Detector Systems Software Group.
"""

from odin.http.handlers.base import BaseApiHandler, validate_api_request, API_VERSION


class AsyncApiHandler(BaseApiHandler):
    """Class for handling asynchrounous API requests.

    This class handles asynchronous API requests, that is when the ODIN server is being
    used with Tornado and python versions the implement native async behaviour.
    """

    @validate_api_request(API_VERSION)
    async def get(self, subsystem, path=''):
        """Handle an API GET request.

        :param subsystem: subsystem element of URI, defining adapter to be called
        :param path: remaining URI path to be passed to adapter method
        """
        adapter = self.route.adapter(subsystem)
        if adapter.is_async:
            response = await adapter.get(path, self.request)
        else:
            response = adapter.get(path, self.request)

        self.respond(response)

    @validate_api_request(API_VERSION)
    async def post(self, subsystem, path=''):
        """Handle an API POST request.

        :param subsystem: subsystem element of URI, defining adapter to be called
        :param path: remaining URI path to be passed to adapter method
        """
        adapter = self.route.adapter(subsystem)
        if adapter.is_async:
            response = await adapter.post(path, self.request)
        else:
            response = adapter.post(path, self.request)

        self.respond(response)

    @validate_api_request(API_VERSION)
    async def put(self, subsystem, path=''):
        """Handle an API PUT request.

        :param subsystem: subsystem element of URI, defining adapter to be called
        :param path: remaining URI path to be passed to adapter method
        """
        adapter = self.route.adapter(subsystem)
        if adapter.is_async:
            response = await adapter.put(path, self.request)
        else:
            response = adapter.put(path, self.request)
        self.respond(response)

    @validate_api_request(API_VERSION)
    async def delete(self, subsystem, path=''):
        """Handle an API DELETE request.

        :param subsystem: subsystem element of URI, defining adapter to be called
        :param path: remaining URI path to be passed to adapter method
        """
        adapter = self.route.adapter(subsystem)
        if adapter.is_async:
            response = await adapter.delete(path, self.request)
        else:
            response = adapter.delete(path, self.request)
        self.respond(response)
