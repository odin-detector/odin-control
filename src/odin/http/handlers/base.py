"""Base API handler for the ODIN server.

This module implements the base API handler functionality from which both the concrete
synchronous and asynchronous API handler implementations inherit.

Tim Nicholls, STFC Detector Systems Software Group.
"""

import tornado.web

from odin.adapters.adapter import ApiAdapterResponse
from odin.util import wrap_result
API_VERSION = 0.1


class ApiError(Exception):
    """Simple exception class for API-related errors."""


def validate_api_request(required_version):
    """Validate an API request to the ApiHandler.

    This decorator checks that API version in the URI of a requst is correct and that the subsystem
    is registered with the application dispatcher; responds with a 400 error if not
    """
    def decorator(func):
        def wrapper(_self, *args, **kwargs):
            # Extract version as first argument
            version = args[0]
            subsystem = args[1]
            rem_args = args[2:]
            if version != str(required_version):
                _self.respond(ApiAdapterResponse(
                    "API version {} is not supported".format(version),
                    status_code=400))
                return wrap_result(None)
            if not _self.route.has_adapter(subsystem):
                _self.respond(ApiAdapterResponse(
                    "No API adapter registered for subsystem {}".format(subsystem),
                    status_code=400))
                return wrap_result(None)
            return func(_self, subsystem, *rem_args, **kwargs)
        return wrapper
    return decorator


class BaseApiHandler(tornado.web.RequestHandler):
    """API handler to transform requests into appropriate adapter calls.

    This handler maps incoming API requests into the appropriate calls to methods
    in registered adapters. HTTP GET, PUT and DELETE verbs are supported. The class
    also enforces a uniform response with the appropriate Content-Type header.
    """

    def __init__(self, *args, **kwargs):
        """Construct the BaseApiHandler object.

        This method just calls the base class constructor and sets the route object to None.
        """
        self.route = None
        super(BaseApiHandler, self).__init__(*args, **kwargs)

    def initialize(self, route):
        """Initialize the API handler.

        :param route: ApiRoute object calling the handler (allows adapters to be resolved)
        """
        self.route = route

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

    def get(self, subsystem, path=''):
        """Handle an API GET request.

        This is an abstract method which must be implemented by derived classes.

        :param subsystem: subsystem element of URI, defining adapter to be called
        :param path: remaining URI path to be passed to adapter method
        """
        raise NotImplementedError()

    def post(self, subsystem, path=''):
        """Handle an API POST request.

        This is an abstract method which must be implemented by derived classes.

        :param subsystem: subsystem element of URI, defining adapter to be called
        :param path: remaining URI path to be passed to adapter method
        """
        raise NotImplementedError()

    def put(self, subsystem, path=''):
        """Handle an API PUT request.

        This is an abstract method which must be implemented by derived classes.

        :param subsystem: subsystem element of URI, defining adapter to be called
        :param path: remaining URI path to be passed to adapter method
        """
        raise NotImplementedError()

    def delete(self, subsystem, path=''):
        """Handle an API DELETE request.

        This is an abstract method which must be implemented by derived classes.

        :param subsystem: subsystem element of URI, defining adapter to be called
        :param path: remaining URI path to be passed to adapter method
        """
        raise NotImplementedError()
