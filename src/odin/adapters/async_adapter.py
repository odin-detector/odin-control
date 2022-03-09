"""
odin.adapters.adapter.py - base asynchronous API adapter implmentation for the ODIN server.

Tim Nicholls, STFC Detector Systems Software Group
"""

import asyncio
import logging

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