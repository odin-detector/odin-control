"""Proxy adapter class for the ODIN server.

This class implements a simple asynchronous proxy adapter, allowing requests to be proxied to
one or more remote HTTP resources, typically further ODIN servers.

Tim Nicholls, STFC Application Engineering Group.
"""
import logging
import time
import tornado

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
        self.error_string = ''
        self.last_update = ''
        self.data = {}

        # Build a parameter tree representation of the proxy target
        self.param_tree = ParameterTree({
            'url': self.url,
            'data': (self._get_data, None),
            'status_code': (self._get_status_code, None),
            'error': (self._get_error_string, None),
            'last_update': (self._get_last_update, None),
        })

        # Create an HTTP client instance and set up default request headers
        self.http_client = tornado.httpclient.HTTPClient()
        self.request_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def _update(self):
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
                self.url, headers=self.request_headers,
                request_timeout=self.request_timeout
            )
            # Update status code and data accordingly
            self.status_code = response.code
            self.data = tornado.escape.json_decode(response.body)

            logging.debug("Proxy target {} fetch succeeded: {} {}".format(
                self.name, self.status_code, self.data
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

        self._update()
        return self.data


class ProxyAdapter(ApiAdapter):

    def __init__(self, **kwargs):

        super(ProxyAdapter, self).__init__(**kwargs)

        request_timeout = None
        if 'request_timeout' in kwargs:
            try:
                request_timeout = float(kwargs['request_timeout'])
                logging.debug('ProxyAdapter request timeout set to {:f} secs'.format(
                    request_timeout
                ))
            except ValueError:
                logging.error("Illegal timeout specified for ProxyAdapter: {}".format(
                    kwargs['request_timeout']
                ))

        self.targets = []
        if 'targets' in kwargs:
            for target_str in kwargs['targets'].split(','):
                (target, url) = target_str.strip().split('=')
                self.targets.append(ProxyTarget(target, url, request_timeout))

        self.param_tree = ParameterTree(
            {target.name: target.param_tree for target in self.targets}
        )
        logging.debug("ProxyAdapter with {:d} targets loaded".format(len(self.targets)))

    @request_types('application/json')
    @response_types('application/json', default='application/json')
    def get(self, path, request):

        try:
            logging.debug("get: path {}".format(path))
            response = self.param_tree.get(path)
            status_code = 200
        except ParameterTreeError as e:
            response = {'error': str(e)}
            status_code = 400

        return ApiAdapterResponse(response, status_code=status_code)
