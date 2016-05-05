"""
adapter.py - EXCALIBUR API adapter for the ODIN server

Tim Nicholls, STFC Application Engineering Group
"""

import logging
from odin.adapters.adapter import ApiAdapter, ApiAdapterResponse, request_types, response_types


class ExcaliburAdapter(ApiAdapter):

    """
    ExcaliburAdapter class

    This class provides the adapter interface between the ODIN server and the EXCALIBUR detector system,
    transforming the REST-like API HTTP verbs into the appropriate EXCALIBUR detector control actions
    """

    def __init__(self, **kwargs):

        """Initialise the ExcaliburAdapter object"""

        super(ExcaliburAdapter, self).__init__(**kwargs)
        logging.debug('ExcaliburAdapter loaded')


    @request_types('application/json')
    @response_types('application/json', default='application/json')
    def get(self, path, request):

        """
        Implementation of the HTTP GET verb for ExcaliburAdapter

        :param path: URI path of the GET request
        :param request: Tornado HTTP request object
        :return: ApiAdapterResponse object to be returned to the client
        """

        response = {'response' : '{}: GET on path {}'.format(self.name, path)}
        status_code = 200

        logging.debug(response)

        return ApiAdapterResponse(response, status_code=status_code)

    @request_types('application/json')
    @response_types('application/json', default='application/json')
    def put(self, path, request):

        """
        Implementation of the HTTP PUT verb for ExcaliburAdapter

        :param path: URI path of the PUT request
        :param request: Tornado HTTP request object
        :return: ApiAdapterResponse object to be returned to the client
        """

        response = {'response': '{}: PUT on path {}'.format(self.name, path)}
        status_code = 200

        logging.debug(response)

        return ApiAdapterResponse(response, status_code=status_code)


    @request_types('application/json')
    @response_types('application/json', default='application/json')
    def delete(self, path, request):
        """
        Implementation of the HTTP DELETE verb for ExcaliburAdapter

        :param path: URI path of the DELETE request
        :param request: Tornado HTTP request object
        :return: ApiAdapterResponse object to be returned to the client
        """

        response = {'response': '{}: DELETE on path {}'.format(self.name, path)}
        status_code = 200

        logging.debug(response)

        return ApiAdapterResponse(response, status_code=status_code)
