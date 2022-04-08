"""
odin.adapters.adapter.py - base asynchronous API adapter implmentation for the ODIN server.

Tim Nicholls, STFC Detector Systems Software Group
"""

import asyncio
import logging
import inspect

from odin.adapters.adapter import ApiAdapter, ApiAdapterResponse


class AsyncApiAdapter(ApiAdapter):
    """
    Asynchronous API adapter base class.

    This class defines the basis for all async API adapters and provides default
    methods for the required HTTP verbs in case the derived classes fail to
    implement them, returning an error message and 400 code.
    """

    is_async = True

    def __init__(self, **kwargs):
        """Initialise the AsyncApiAdapter object.

        :param kwargs: keyword argument list that is copied into options dictionary
        """
        super(AsyncApiAdapter, self).__init__(**kwargs)

    def __await__(self):
        """Make AsyncApiAdapter objects awaitable.

        This magic method makes the instantiation of AsyncApiAdapter objects awaitable. This allows
        any underlying async and awaitable attributes, e.g. an AsyncParameterTree, to be correctly
        awaited when the adapter is loaded."""
        async def closure():
            """Await all async attributes of the adapter."""
            awaitable_attrs = [attr for attr in self.__dict__.values() if inspect.isawaitable(attr)]
            await asyncio.gather(*awaitable_attrs)
            return self

        return closure().__await__()

    async def initialize(self, adapters):
        """Initialize the AsyncApiAdapter after it has been registered by the API Route.

        This is an abstract implementation of the initialize mechinism that allows
        an adapter to receive a list of loaded adapters, for Inter-adapter communication.
        :param adapters: a dictionary of the adapters loaded by the API route.
        """

        pass

    async def cleanup(self):
        """Clean up adapter state.

        This is an abstract implementation of the cleanup mechanism provided to allow adapters
        to clean up their state (e.g. disconnect cleanly from the device being controlled, set
        some status message).
        """
        pass

    async def get(self, path, request):
        """Handle an HTTP GET request.

        This method is an abstract implementation of the GET request handler for AsyncApiAdapter.

        :param path: URI path of resource
        :param request: HTTP request object passed from handler
        :return: ApiAdapterResponse container of data, content-type and status_code
        """
        logging.debug('GET on path %s from %s: method not implemented by %s',
                      path, request.remote_ip, self.name)
        await asyncio.sleep(0)
        response = "GET method not implemented by {}".format(self.name)
        return ApiAdapterResponse(response, status_code=400)

    async def post(self, path, request):
        """Handle an HTTP POST request.

        This method is an abstract implementation of the POST request handler for AsyncApiAdapter.

        :param path: URI path of resource
        :param request: HTTP request object passed from handler
        :return: ApiAdapterResponse container of data, content-type and status_code
        """
        logging.debug('POST on path %s from %s: method not implemented by %s',
                      path, request.remote_ip, self.name)
        await asyncio.sleep(0)
        response = "POST method not implemented by {}".format(self.name)
        return ApiAdapterResponse(response, status_code=400)

    async def put(self, path, request):
        """Handle an HTTP PUT request.

        This method is an abstract implementation of the PUT request handler for AsyncApiAdapter.

        :param path: URI path of resource
        :param request: HTTP request object passed from handler
        :return: ApiAdapterResponse container of data, content-type and status_code
        """
        logging.debug('PUT on path %s from %s: method not implemented by %s',
                      path, request.remote_ip, self.name)
        await asyncio.sleep(0)
        response = "PUT method not implemented by {}".format(self.name)
        return ApiAdapterResponse(response, status_code=400)

    async def delete(self, path, request):
        """Handle an HTTP DELETE request.

        This method is an abstract implementation of the DELETE request handler for ApiAdapter.

        :param path: URI path of resource
        :param request: HTTP request object passed from handler
        :return: ApiAdapterResponse container of data, content-type and status_code
        """
        logging.debug('DELETE on path %s from %s: method not implemented by %s',
                      path, request.remote_ip, self.name)
        await asyncio.sleep(0)
        response = "DELETE method not implemented by {}".format(self.name)
        return ApiAdapterResponse(response, status_code=400)
