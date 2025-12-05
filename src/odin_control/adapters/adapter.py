"""Base API adapter implementation for odin-control.

Tim Nicholls, STFC Detector System Software Group
"""

import logging

from tornado.escape import json_decode

from odin_control.adapters.base_controller import BaseError
from odin_control.adapters.request import ApiAdapterRequest  # noqa: F401
from odin_control.adapters.response import ApiAdapterResponse
from odin_control.adapters.util import (
    request_types,
    require_controller,
    response_types,
    wants_metadata,
)


class ApiAdapter():
    """API adapter base class.

    This class defines the basis for all API adapters and provides default methods for supported
    HTTP verbs and for lifecycle management. Dervied adapters can either override these methods
    explciitly to provide custom behavior, or adopt the adapter-controller pattern by specifying
    controller and error clases, and allowing default methods in this class to interface requests
    to the controller.
    """

    is_async = False
    version = "unknown"  # Derived classes should override this with a relevant version string

    # Derived classes can specify controller and error classes to use
    controller_cls = None
    error_cls = BaseError

    def __init__(self, **kwargs):
        """Initialise the ApiAdapter object.

        This method initialises the adapter, loading any keyword arguments into the options
        dictionary, and instantiating the controller if a controller class has been specified

        :param kwargs: keyword argument list that is copied into options dictionary
        """
        self.name = type(self).__name__

        # Load any keyword arguments into the adapter options dictionary
        self.options = {}
        for kw in kwargs:
            self.options[kw] = kwargs[kw]

        # Instantiate the controller if a controller class has been specified
        if self.controller_cls:
            self.controller = self.controller_cls(self.options)
        else:
            self.controller = None

        logging.debug("%s loaded", self.name)

    def initialize(self, adapters):
        """Initialize the ApiAdapter after it has been registered by the API Route.

        This method allows the adapter to perform any initialization that requires access to other
        loaded adapters. It receives a dictionary of loaded adapters from the API route and passes
        them to the controller's initialize method, if a controller has been configured.

        :param adapters: a dictionary of the adapters loaded by the API route.
        """
        logging.debug("%s initialize called with %d adapters", self.name, len(adapters))

        # Build a dictionary of other adapters excluding self
        adapters = {name: adapter for name, adapter in adapters.items() if adapter is not self}

        # Initialize the controller with access to other adapters
        if self.controller:
            try:
                self.controller.initialize(adapters)
            except AttributeError:
                logging.warning("%s controller has no initialize method", self.name)
        else:
            logging.warning("%s has no controller configured", self.name)


    @response_types("application/json", default="application/json")
    @require_controller
    def get(self, path, request):
        """Handle an HTTP GET request.

        This method is a default implementation of the GET request handler for adapters. It calls
        the get method of the controller and returns the result. Error handling is provided to
        catch controller errors and return appropriate error responses.

        :param path: URI path of resource
        :param request: HTTP request object passed from handler
        :return: ApiAdapterResponse container of data, content-type and status_code
        """
        content_type = "application/json"

        try:
            response = self.controller.get(path, wants_metadata(request))
            status_code = 200
        except self.error_cls as error:
            response = {"error": str(error)}
            status_code = 400

        return ApiAdapterResponse(response, content_type=content_type, status_code=status_code)

    @request_types("application/json", "application/vnd.odin-native")
    @response_types("application/json", default="application/json")
    @require_controller
    def put(self, path, request):
        """Handle an HTTP PUT request.

        This method is a default implementation of the PUT request handler for adapter. It calls
        the set method of the controller with the specified data and returns the result of a
        subsequent get call. Error handling is provided to catch controller errors and return
        appropriate error responses.

        :param path: URI path of resource
        :param request: HTTP request object passed from handler
        :return: ApiAdapterResponse container of data, content-type and status_code
        """
        content_type = "application/json"

        try:
            data = json_decode(request.body)
            self.controller.set(path, data)
            response = self.controller.get(path)
            status_code = 200
        except self.error_cls as error:
            response = {"error": str(error)}
            status_code = 400
        except NotImplementedError:
            response = {
                "error": f"{self.name} does not support PUT requests"
            }
            status_code = 405
        except (TypeError, ValueError) as error:
            response = {"error": f"Failed to decode PUT request body: {str(error)}"}
            status_code = 400

        return ApiAdapterResponse(response, content_type=content_type, status_code=status_code)


    @request_types("application/json", "application/vnd.odin-native")
    @response_types("application/json", default="application/json")
    @require_controller
    def post(self, path, request):
        """Handle an HTTP POST request.

        This method is a default implementation of the POST request handler for adapters. It calls
        the create method of the controller and returns the result. Error handling is provided to
        catch controller errors and return appropriate error responses.

        :param path: URI path of resource
        :param request: HTTP request object passed from handler
        :return: ApiAdapterResponse container of data, content-type and status_code
        """
        content_type = "application/json"

        try:
            data = json_decode(request.body)
            response = self.controller.create(path, data)
            status_code = 200
        except self.error_cls as error:
            response = {"error": str(error)}
            status_code = 400
        except NotImplementedError:
            response = {
                "error": f"{self.name} does not support POST requests"
            }
            status_code = 405
        except (TypeError, ValueError) as error:
            response = {"error": f"Failed to decode POST request body: {str(error)}"}
            status_code = 400

        return ApiAdapterResponse(response, content_type=content_type, status_code=status_code)

    @response_types("application/json", default="application/json")
    @require_controller
    def delete(self, path, request):
        """Handle an HTTP DELETE request.

        This method is a default implementation of the DELETE request handler for adapters. It calls
        the delete method of the controller and returns the result. Error handling is provided to
        catch controller errors and return appropriate error responses.

        :param path: URI path of resource
        :param request: HTTP request object passed from handler
        :return: ApiAdapterResponse container of data, content-type and status_code
        """
        content_type = "application/json"

        try:
            response = self.controller.delete(path)
            status_code = 200
        except self.error_cls as error:
            response = {"error": str(error)}
            status_code = 400
        except NotImplementedError:
            response = {
                "error": f"{self.name} does not support DELETE requests"
            }
            status_code = 405

        return ApiAdapterResponse(response, content_type=content_type, status_code=status_code)

    def cleanup(self):
        """Clean up adapter state.

        This is a default implementation of the cleanup mechanism provided to allow adapters
        to clean up their state (e.g. disconnect cleanly from the device being controlled, set
        some status message).
        """
        logging.debug("%s cleanup called",  self.name)

        # If a controller is configured, call its cleanup method
        if self.controller:
            try:
                self.controller.cleanup()
            except AttributeError:
                logging.warning("%s controller has no cleanup method", self.name)
        else:
            logging.warning("%s has no controller configured", self.name)


