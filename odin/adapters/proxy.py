"""Proxy adapter class for the ODIN server.

This class implements a simple asynchronous proxy adapter, allowing requests to be proxied to
one or more remote HTTP resources, typically further ODIN servers.

Tim Nicholls, STFC Application Engineering Group.
"""
import logging
import time
import tornado
import tornado.httpclient
from tornado.escape import json_decode

from odin.adapters.adapter import ApiAdapter, ApiAdapterResponse, request_types, response_types
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError


class ProxyTarget(object):
    """
    Proxy adapter target class.

    This class implements a proxy target, its parameter tree and associated
    status information for use in the ProxyAdapter.
    """

    def __init__(self, name, url, request_timeout):
        """
        Initalise the ProxyTarget object.

        Sets up the default state of the target object, builds the
        appropriate parameter tree to be handled by the containing adapter
        and sets up the HTTP client for making requests to the target.
        """
        self.name = name
        self.url = url
        self.request_timeout = request_timeout

        # Initialise default state
        self.status_code = 0
        self.error_string = 'OK'
        self.last_update = 'unknown'
        self.data = {}
        self.counter = 0

        # Build a parameter tree representatio of the proxy target status
        self.status_param_tree = ParameterTree({
            'url': self.url,
            'status_code': (self._get_status_code, None),
            'error': (self._get_error_string, None),
            'last_update': (self._get_last_update, None),
        })

        # Build a parameter tree representation of the proxy target data
        self.data_param_tree = ParameterTree((self._get_data, self._set_data))

        # Create an HTTP client instance and set up default request headers
        self.http_client = tornado.httpclient.HTTPClient()
        self.request_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def update(self, path):
        """
        Update the proxy target with new data.

        This internal method updates the proxy target with new data by
        issuing a client request to the specified URL. The associated
        status information is updated according to the success or failure
        of the request.
        """

        try:
            # Request data from the target
            response = self.http_client.fetch(
                self.url + path, headers=self.request_headers,
                request_timeout=self.request_timeout
            )            
            # Update status code and data accordingly
            self.status_code = response.code
            self.error_string = 'OK'
            response_body = tornado.escape.json_decode(response.body)
            data_copy = self.data  # reference for modification
            if path:  # TODO: write unit test that tests this path logic
                path_elems = path.split('/')
                for elem in path_elems[:-1]:
                    data_copy = data_copy[elem]
            for key in response_body:
                new_elem = response_body[key]
                data_copy[key] = new_elem
            logging.debug("Proxy target {} fetch succeeded: {} {}".format(
                self.name, self.status_code, self.data_param_tree.get(path)
            ))

        except tornado.httpclient.HTTPError as http_err:
            # Handle HTTP errors, updating status information and reporting error
            self.status_code = http_err.code
            self.error_string = http_err.message
            logging.error("Proxy target {} fetch failed: {} {}".format(
                self.name, self.status_code, self.error_string
            ))

        except Exception as other_err:
            # Handle other errors, updating status information and reporting error
            self.status_code = 502
            self.error_string = str(other_err)
            logging.error("Proxy target {} fetch failed: {} {}".format(
                self.name, self.status_code, self.error_string
            ))

        # Update the timestamp of the last request in standard format
        self.last_update = tornado.httputil.format_timestamp(time.time())

    def _get_status_code(self):
        """
        Get the target request status code.

        This internal method is used to retrieve the status code
        of the last target update request for use in the parameter
        tree.
        """
        return self.status_code

    def _get_error_string(self):
        """
        Get the target request error string.

        This internal method is used to retrieve the error string
        of the last target update request for use in the parameter
        tree.
        """
        return self.error_string

    def _get_last_update(self):
        """
        Get the target request last update timestamp.

        This internal method is used to retrieve the timestamp
        of the last target update request for use in the parameter
        tree.
        """
        return self.last_update

    def _get_data(self):
        """
        Get the target request data.

        This internal method is used to retrieve the target updated during last call to update(),
        for use in the parameter tree.
        """
        return self.data

    def _set_data(self, data):  # TODO: test set data methods

        logging.debug("ProxyTarget {} set with data {}".format(self.name, data))


class ProxyAdapter(ApiAdapter):
    """
    Proxy adapter class for ODIN server.

    This class implements a proxy adapter, allowing ODIN server to forward requests to
    other HTTP services.
    """

    def __init__(self, **kwargs):
        """
        Initialise the ProxyAdapter.

        This constructor initialises the adapter instance, parsing configuration
        options out of the keyword arguments it is passed. A ProxyTarget object is
        instantiated for each target specified in the options.

         :param kwargs: keyword arguments specifying options
        """

        # Initialise base class
        super(ProxyAdapter, self).__init__(**kwargs)

        # Set the HTTP request timeout if present in the options
        request_timeout = None
        if 'request_timeout' in kwargs:
            try:
                request_timeout = float(kwargs['request_timeout'])
                logging.debug('ProxyAdapter request timeout set to {} secs'.format(
                    request_timeout
                ))
            except ValueError:
                logging.error("Illegal timeout specified for ProxyAdapter: {}".format(
                    kwargs['request_timeout']
                ))

        # Parse the list of target-URL pairs from the options, instantiating a ProxyTarget
        # object for each target specified.
        self.targets = []
        if 'targets' in kwargs:
            for target_str in kwargs['targets'].split(','):
                try:
                    (target, url) = target_str.strip().split('=')
                    self.targets.append(ProxyTarget(target, url, request_timeout))
                except ValueError:
                    logging.error("Illegal target specification for ProxyAdapter: {}".format(
                        target_str.strip()
                    ))

        # Issue an error message if no targets were loaded
        if self.targets:
            logging.debug("ProxyAdapter with {:d} targets loaded".format(len(self.targets)))
        else:
            logging.error("Failed to resolve targets for ProxyAdapter")

        # Construct the parameter tree returned by this adapter
        tree = { 'status' : {} }
        for target in self.targets:
            tree['status'][target.name] = target.status_param_tree
            tree[target.name] = target.data_param_tree

        self.param_tree = ParameterTree(tree)

    @request_types('application/json')
    @response_types('application/json', default='application/json')
    def get(self, path, request):
        """
        Handle an HTTP GET request.

        This method handles an HTTP GET request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        # Update the target specified in the path, or all targets if none specified
        if "/" in path:
            path_elem, target_path = path.split('/', 1)
        else:
            path_elem = path.split('/')[0]
            target_path = ""
        for target in self.targets:
            if path_elem == '' or path_elem == target.name:                
                target.update(target_path)
                
        # Build the response from the adapter parameter tree
        try:
            response = self.param_tree.get(path)
            status_code = 200
        except ParameterTreeError as param_tree_err:
            response = {'error': str(param_tree_err)}
            status_code = 400

        return ApiAdapterResponse(response, status_code=status_code)

    @request_types('application/json')
    @response_types('application/json', default='application/json')
    def put(self, path, request):  # TODO: write Unit Test for put methods
        """Handle an HTTP PUT request.

        This method handles an HTTP PUT request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        try:
            data = json_decode(request.body)
            self.param_tree.set(path, data)
            response = self.param_tree.get(path)
            status_code = 200
        except ParameterTreeError as e:
            response = {'error': str(e)}
            status_code = 400
        except (TypeError, ValueError) as e:
            response = {'error': 'Failed to decode PUT request body: {}'.format(str(e))}
            status_code = 400

        return ApiAdapterResponse(response, status_code=status_code)