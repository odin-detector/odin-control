"""System info adapter class for the ODIN server.

This class implements a system information adapter for the ODIN server, providing system-level
information about the system to clients.

Tim Nicholls, STFC Application Engineering
"""
import logging
import tornado
import platform
import time
from future.utils import with_metaclass

from odin.adapters.adapter import ApiAdapter, ApiAdapterResponse, request_types, response_types
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from odin._version import get_versions


class SystemInfoAdapter(ApiAdapter):
    """System info adapter class for the ODIN server.

    This adapter provides ODIN clients with information about the server and the system that it is
    running on.
    """

    def __init__(self, **kwargs):
        """Initialize the SystemInfoAdapter object.

        This constructor initializes the SystemInfoAdapter object, including resolving any
        system-level information that the adapter can provide to clients subsequently.

        :param kwargs: keyword arguments specifying options
        """
        super(SystemInfoAdapter, self).__init__(**kwargs)
        self.system_info = SystemInfo()
        logging.debug('SystemInfoAdapter loaded')

    @response_types('application/json', default='application/json')
    def get(self, path, request):
        """Handle an HTTP GET request.

        This method handles an HTTP GET request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        try:
            response = self.system_info.get(path)
            status_code = 200
        except ParameterTreeError as e:
            response = {'error': str(e)}
            status_code = 400

        logging.debug(response)
        content_type = 'application/json'

        return ApiAdapterResponse(response, content_type=content_type,
                                  status_code=status_code)

    @request_types('application/json')
    @response_types('application/json', default='application/json')
    def put(self, path, request):
        """Handle an HTTP PUT request.

        This method handles an HTTP PUT request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        response = {'response': 'SystemInfoAdapter: PUT on path {}'.format(path)}
        content_type = 'application/json'
        status_code = 200

        logging.debug(response)

        return ApiAdapterResponse(response, content_type=content_type,
                                  status_code=status_code)

    def delete(self, path, request):
        """Handle an HTTP DELETE request.

        This method handles an HTTP DELETE request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        response = 'SystemInfoAdapter: DELETE on path {}'.format(path)
        status_code = 200

        logging.debug(response)

        return ApiAdapterResponse(response, status_code=status_code)


class Singleton(type):
    """Singleton metaclass for use with SystemInfo to ensure only one instance is created."""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """Ensure only a single instance of any class is created."""
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class SystemInfo(with_metaclass(Singleton, object)):
    """SystemInfo - class that extracts and stores information about system-level parameters."""

    # __metaclass__ = Singleton

    def __init__(self):
        """Initialise the SystemInfo object.

        This constructor initlialises the SystemInfo object, extracting various system-level
        parameters and storing them in a parameter tree to be accessible to clients.
        """
        # Store initialisation time
        self.init_time = time.time()

        # Get package version information
        version_info = get_versions()

        # Extract platform information and store in parameter tree
        (system, node, release, version, machine, processor) = platform.uname()
        platform_tree = ParameterTree({
            'system': system,
            'node': node,
            'release': release,
            'version': version,
            'processor': processor
        })

        # Store all information in a parameter tree
        self.param_tree = ParameterTree({
            'odin_version': version_info['version'],
            'tornado_version': tornado.version,
            'platform': platform_tree,
            'server_uptime': (self.get_server_uptime, None),
        })

    def get_server_uptime(self):
        """Get the uptime for the ODIN server.

        This method returns the current uptime for the ODIN server.
        """
        return time.time() - self.init_time

    def get(self, path):
        """Get the parameter tree.

        This method returns the parameter tree for use by clients via the SystemInfo adapter.

        :param path: path to retrieve from tree
        """
        return self.param_tree.get(path)
