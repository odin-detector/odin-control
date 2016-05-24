"""
adapter.py - EXCALIBUR API adapter for the ODIN server.

Tim Nicholls, STFC Application Engineering Group
"""

import logging
from odin.adapters.adapter import ApiAdapter, ApiAdapterResponse, request_types, response_types

from excalibur.detector import ExcaliburDetector, ExcaliburDetectorError


def require_valid_detector(func):
    """Decorator method for request handler methods to check that adapter has valid detector."""
    def wrapper(_self, path, request):
        if _self.detector is None:
            return ApiAdapterResponse(
                'Invalid detector configuration', status_code=500
            )
        return func(_self, path, request)
    return wrapper


class ExcaliburAdapter(ApiAdapter):
    """ExcaliburAdapter class.

    This class provides the adapter interface between the ODIN server and the EXCALIBUR detector
    system, transforming the REST-like API HTTP verbs into the appropriate EXCALIBUR detector
    control actions
    """

    def __init__(self, **kwargs):
        """Initialise the ExcaliburAdapter object.

        :param kwargs: keyword arguments passed to ApiAdapter as options.
        """
        super(ExcaliburAdapter, self).__init__(**kwargs)

        # Parse the FEM connection information out of the adapter options and initialise the
        # detector object
        self.detector = None
        if 'detector_fems' in self.options:
            fems = [tuple(fem.split(':')) for fem in self.options['detector_fems'].split(',')]
            try:
                self.detector = ExcaliburDetector(fems)
                logging.debug('ExcaliburAdapter loaded')
            except ExcaliburDetectorError as e:
                logging.error('ExcaliburAdapter failed to initialise detector: %s', e)
        else:
            logging.warning('No detector FEM option specified in configuration')

    @request_types('application/json')
    @response_types('application/json', default='application/json')
    @require_valid_detector
    def get(self, path, request):
        """Handle an HTTP GET request.

        This method is the implementation of the HTTP GET handler for ExcaliburAdapter.

        :param path: URI path of the GET request
        :param request: Tornado HTTP request object
        :return: ApiAdapterResponse object to be returned to the client
        """
        response = {'response': '{}: GET on path {}'.format(self.name, path)}
        status_code = 200

        logging.debug(response)

        return ApiAdapterResponse(response, status_code=status_code)

    @request_types('application/json')
    @response_types('application/json', default='application/json')
    @require_valid_detector
    def put(self, path, request):
        """Handle an HTTP PUT request.

        This method is the implementation of the HTTP PUT handler for ExcaliburAdapter/

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
    @require_valid_detector
    def delete(self, path, request):
        """Handle an HTTP DELETE request.

        This method is the implementation of the HTTP DELETE verb for ExcaliburAdapter.

        :param path: URI path of the DELETE request
        :param request: Tornado HTTP request object
        :return: ApiAdapterResponse object to be returned to the client
        """
        response = {'response': '{}: DELETE on path {}'.format(self.name, path)}
        status_code = 200

        logging.debug(response)

        return ApiAdapterResponse(response, status_code=status_code)
