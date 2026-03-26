"""Base asynchronous API adapter implmentation for the odin-control.

Tim Nicholls, STFC Detector Systems Software Group
"""

import asyncio
import inspect
import logging

from odin_control.adapters.adapter import (
    ApiAdapter,
    ApiAdapterRequest,  # noqa: F401
    ApiAdapterResponse,
    json_decode,
    request_types,
    require_controller,
    response_types,
    wants_metadata,
)


class AsyncApiAdapter(ApiAdapter):
    """Asynchronous API adapter base class.

    This class defines the basis for all async API adapters and provides default methods for
    supported HTTP verbs and for lifecycle management. Derived adapters can override these
    methods explicitly to provide custom behavior. Through the parent ApiAdapter class, this
    class also supports the adapter-controller pattern; the controller class should be derived from
    AsyncBaseController to provide async behavior during controller initialization.
    """

    # Set flag to indicate that this is an async adapter
    is_async = True

    def __init__(self, **kwargs):
        """Initialise the AsyncApiAdapter object.

        :param kwargs: keyword argument list that is copied into options dictionary
        """
        super(AsyncApiAdapter, self).__init__(**kwargs)

    def __await__(self):
        """Make AsyncApiAdapter objects awaitable.

        This magic method makes the instantiation of AsyncApiAdapter objects awaitable. This allows
        any underlying async and awaitable attributes, e.g. an AsyncBaseController, to be correctly
        awaited when the adapter is loaded.
        """
        async def closure():
            """Await all async attributes of the adapter."""
            awaitable_attrs = [attr for attr in self.__dict__.values() if inspect.isawaitable(attr)]
            await asyncio.gather(*awaitable_attrs)
            return self

        return closure().__await__()

    async def initialize(self, adapters):
        """Initialize the AsyncApiAdapter after it has been registered by the API Route.

        This method allows the adapter to perform any initialization that requires access to other
        loaded adapters. It receives a dictionary of loaded adapters from the API route and passes
        them to the controller's initialize method, if a controller has been configured.

        """
        logging.debug("%s initialize called with %d adapters", self.name, len(adapters))

        # Build a dictionary of other adapters excluding self
        adapters = {name: adapter for name, adapter in adapters.items() if adapter is not self}

        # Initialize the controller with access to other adapters
        if self.controller:
            try:
                await self.controller.initialize(adapters)
            except AttributeError:
                logging.warning("%s controller has no initialize method", self.name)
        else:
            logging.warning("%s has no controller configured", self.name)

    @response_types("application/json", default="application/json")
    @require_controller
    async def get(self, path, request):
        """Handle an HTTP GET request.

        This method is a default implementation of the async GET request handler for adapters. It
        calls the get method of the controller and returns the result. Error handling is provided to
        catch controller errors and return appropriate error responses.

        :param path: URI path of resource
        :param request: HTTP request object passed from handler
        :return: ApiAdapterResponse container of data, content-type and status_code
        """
        content_type = "application/json"

        try:
            response = await self.controller.get(path, wants_metadata(request))
            status_code = 200
        except self.error_cls as error:
            response = {"error": str(error)}
            status_code = 400

        return ApiAdapterResponse(response, content_type=content_type, status_code=status_code)

    @request_types("application/json", "application/vnd.odin-native")
    @response_types("application/json", default="application/json")
    @require_controller
    async def put(self, path, request):
        """Handle an HTTP PUT request.

        This method is a default implementation of the async PUT request handler for adapters. It
        calls the set method of the controller with the specified data and returns the result of a
        subsequent get call. Error handling is provided to catch controller errors and return
        appropriate error responses.

        :param path: URI path of resource
        :param request: HTTP request object passed from handler
        :return: ApiAdapterResponse container of data, content-type and status_code
        """
        content_type = "application/json"

        try:
            data = json_decode(request.body)
            await self.controller.set(path, data)
            response = await self.controller.get(path)
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
    async def post(self, path, request):
        """Handle an HTTP POST request.

        This method is a default implementation of the async POST request handler for adapters. It
        calls the create method of the controller and returns the result. Error handling is provided
        to catch controller errors and return appropriate error responses.

        :param path: URI path of resource
        :param request: HTTP request object passed from handler
        :return: ApiAdapterResponse container of data, content-type and status_code
        """
        content_type = "application/json"

        try:
            data = json_decode(request.body)
            response = await self.controller.create(path, data)
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
    async def delete(self, path, request):
        """Handle an HTTP DELETE request.

        This method is a default implementation of the async DELETE request handler for adapters. It
        calls the delete method of the controller and returns the result. Error handling is provided
        to catch controller errors and return appropriate error responses.

        :param path: URI path of resource
        :param request: HTTP request object passed from handler
        :return: ApiAdapterResponse container of data, content-type and status_code
        """
        content_type = "application/json"

        try:
            response = await self.controller.delete(path)
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

    async def cleanup(self):
        """Clean up adapter state.

        This method is a default implementation of the async cleanup mechanism provided to allow
        adapters to clean up their state (e.g. disconnect cleanly from the device being controlled,
        set some status message).
        """
        logging.debug("%s cleanup called",  self.name)

        # If a controller is configured, call its cleanup method
        if self.controller:
            try:
                await self.controller.cleanup()
            except AttributeError:
                logging.warning("%s controller has no cleanup method", self.name)
        else:
            logging.warning("%s has no controller configured", self.name)

