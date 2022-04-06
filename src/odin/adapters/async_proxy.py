"""
Asynchronous proxy adapter for use in odin-control.

This module implements a simple asynchronous proxy adapter, allowing requests to be proxied to
one or more remote HTTP resources, typically further odin-control instances.

Tim Nicholls, Ashley Neaves STFC Detector Systems Software Group.
"""
import asyncio
import inspect

from tornado.httpclient import AsyncHTTPClient
from odin.util import decode_request_body
from odin.adapters.adapter import (
    ApiAdapterResponse, request_types, response_types, wants_metadata
)
from odin.adapters.async_adapter import AsyncApiAdapter
from odin.adapters.base_proxy import BaseProxyTarget, BaseProxyAdapter


class AsyncProxyTarget(BaseProxyTarget):
    """
    Asynchronous proxy adapter target class.

    This class implements an asynchronous proxy target, its parameter tree and associated
    status information for use in the ProxyAdapter.
    """

    def __init__(self, name, url, request_timeout):
        """
        Initialise the AsyncProxyTarget object.

        This constructor initialises the AsyncProxyTarget, creating an async HTTP client and
        delegating the full initialisation to the base class.


        :param name: name of the proxy target
        :param url: URL of the remote target
        :param request_timeout: request timeout in seconds
        """
        # Create an async HTTP client for use in this target
        self.http_client = AsyncHTTPClient()

        # Initialise the base class
        super(AsyncProxyTarget, self).__init__(name, url, request_timeout)

    def __await__(self):
        """
        Make AsyncProxyTarget objects awaitable.

        This magic method makes the instantation of AsyncProxyTarget objects awaitable. This allows
        the async calls to remote_get, used to populate the data and metadata trees from the remote
        target, to be awaited.
        """
        async def closure():
            """Await the calls to the remote target to populate and data and metadata tress."""
            await self.remote_get()
            await self.remote_get(get_metadata=True)
            return self

        return closure().__await__()

    async def remote_get(self, path='', get_metadata=False):
        """
        Get data from the remote target.

        This async method requests data from the remote target by issuing a GET request to the
        target URL, and then updates the local proxy target data and status information according to
        the response. The detailed handling of this is implemented by the base class.

        :param path: path to data on remote target
        :param get_metadata: flag indicating if metadata is to be requested
        """
        await super(AsyncProxyTarget, self).remote_get(path, get_metadata)

    async def remote_set(self, path, data):
        """
        Set data on the remote target.

        This async method sends data to the remote target by issuing a PUT request to the target
        URL, and then updates the local proxy target data and status information according to the
        response. The detailed handling of this is implemented by the base class.

        :param path: path to data on remote target
        :param data: data to set on remote target
        """
        await super(AsyncProxyTarget, self).remote_set(path, data)

    async def _send_request(self, request, path, get_metadata=False):
        """
        Send a request to the remote target and update data.

        This internal async method sends a request to the remote target using the HTTP client
        and handles the response, updating target data accordingly.

        :param request: HTTP request to transmit to target
        :param path: path of data being updated
        :param get_metadata: flag indicating if metadata is to be requested
        """
        # Send the request to the remote target, handling any exceptions that occur
        try:
            response = await self.http_client.fetch(request)
        except Exception as fetch_exception:
            # Set the response to the exception so it can be handled during response resolution
            response = fetch_exception

        # Process the response from the target, updating data as appropriate
        self._process_response(response, path, get_metadata)


class AsyncProxyAdapter(AsyncApiAdapter, BaseProxyAdapter):
    """
    Asynchronous proxy adapter class for odin-control.

    This class implements a proxy adapter, allowing odin-control to forward requests to
    other HTTP services.
    """

    def __init__(self, **kwargs):
        """
        Initialise the AsyncProxyAdapter.

        This constructor initialises the adapter instance. The base class adapter is initialised
        with the keyword arguments and then the proxy targets and paramter tree initialised by the
        proxy adapter mixin.

        :param kwargs: keyword arguments specifying options
        """
        # Initialise the base class
        super(AsyncProxyAdapter, self).__init__(**kwargs)

        # Initialise the proxy targets and parameter trees
        self.initialise_proxy(AsyncProxyTarget)

    def __await__(self):
        """
        Make AsyncProxyAdapter objects awaitable.

        This magic method makes the instantation of AsyncProxyAdapter objects awaitable. This allows
        the async proxy targets to be awaited at initialisation.
        """

        async def closure():
            """Construct a list of awaitable attributes and targets and await initialisation."""
            awaitables = [attr for attr in self.__dict__.values() if inspect.isawaitable(attr)]
            awaitables += [target for target in self.targets if inspect.isawaitable(target)]
            await asyncio.gather(*awaitables)
            return self

        return closure().__await__()

    @response_types('application/json', default='application/json')
    async def get(self, path, request):
        """
        Handle an HTTP GET request.

        This async method handles an HTTP GET request, returning a JSON response. The request is
        passed to the adapter proxy and resolved into responses from the requested proxy targets.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        get_metadata = wants_metadata(request)

        await asyncio.gather(*self.proxy_get(path, get_metadata))
        (response, status_code) = self._resolve_response(path, get_metadata)

        return ApiAdapterResponse(response, status_code=status_code)

    @request_types("application/json", "application/vnd.odin-native")
    @response_types('application/json', default='application/json')
    async def put(self, path, request):
        """
        Handle an HTTP PUT request.

        This async method handles an HTTP PUT request, returning a JSON response. The request is
        passed to the adapter proxy to set data on the remote targets and resolved into responses
        from those targets.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        # Decode the request body from JSON, handling and returning any errors that occur. Otherwise
        # send the PUT request to the remote target
        try:
            body = decode_request_body(request)
        except (TypeError, ValueError) as type_val_err:
            response = {'error': 'Failed to decode PUT request body: {}'.format(str(type_val_err))}
            status_code = 415
        else:
            await asyncio.gather(*self.proxy_set(path, body))
            (response, status_code) = self._resolve_response(path)

        return ApiAdapterResponse(response, status_code=status_code)
