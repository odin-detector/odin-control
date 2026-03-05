"""API request handler for odin-control.

This module implements the API request handler used by odin-control to pass API calls to adapters.

Tim Nicholls, STFC Detector Systems Software Group.
"""
from odin_control.adapters.adapter import ApiAdapterResponse
from odin_control.adapters.util import wrap_result
from odin_control.http.handlers.cors_request import CorsRequestHandler


class ApiError(Exception):
    """Simple exception class for API-related errors."""


def validate_api_request(func):
    """Validate an API request to the ApiHandler.

    This decorator checks that, if API versioning is enabled, the version element of the URI of a
    request is correct and that the subsystem is registered with the application dispatcher; it
    responds with a 400 error if not.
    """
    def wrapper(_self, *args, **kwargs):

        # If API versioning is enabled, extract the version as first argument and validate it
        if _self.route.api_version:
            version = args[0]
            args = args[1:]
            if version != _self.route.api_version:
                _self.respond(ApiAdapterResponse(
                    "API version {} is not supported".format(version),
                    status_code=400))
                return wrap_result(None)

        # Extract the subsystem and remaining arguments
        subsystem = args[0]
        rem_args = args[1:]
        if not _self.route.has_adapter(subsystem):
            _self.respond(ApiAdapterResponse(
                "No API adapter registered for subsystem {}".format(subsystem),
                status_code=400))
            return wrap_result(None)

        return func(_self, subsystem, *rem_args, **kwargs)

    return wrapper


class ApiHandler(CorsRequestHandler):
    """API handler to transform requests into appropriate adapter calls.

    This handler maps incoming API requests onto the appropriate calls to methods in registered
    adapters. HTTP GET, PUT, POST, DELETE and OPTIONS verbs are supported. The handler also enforces
    a uniform response with the appropriate Content-Type header.
    """

    def respond(self, response):
        """Respond to an API request.

        This method transforms an ApiAdapterResponse object into the appropriate request handler
        response, setting the HTTP status code and content type for a response to an API request
        and validating the content of the response against the appropriate type.

        :param response: ApiAdapterResponse object containing response
        """
        self.set_status(response.status_code)
        self.set_header('Content-Type', response.content_type)

        data = response.data

        if response.content_type == 'application/json':
            if not isinstance(response.data, (str, dict)):
                raise ApiError(
                    'A response with content type application/json must have str or dict data'
                )

        self.write(data)

    @validate_api_request
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

    @validate_api_request
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

    @validate_api_request
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

    @validate_api_request
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

