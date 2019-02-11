"""
odin.adapters.adapter.py - base API adapter implmentation for the ODIN server.

Tim Nicholls, STFC Application Engineering Group
"""

import logging


class ApiAdapter(object):
    """
    API adapter base class.

    This class defines the basis for all API adapters and provides default
    methods for the required HTTP verbs in case the derived classes fail to
    implement them, returning an error message and 400 code.
    """

    def __init__(self, **kwargs):
        """Initialise the ApiAdapter object.

        :param kwargs: keyword argument list that is copied into options dictionary
        """
        self.name = type(self).__name__

        # Load any keyword arguments into the adapter options dictionary
        self.options = {}
        for kw in kwargs:
            self.options[kw] = kwargs[kw]

    def get(self, path, request):
        """Handle an HTTP GET request.

        This method is an abstract implementation of the GET request handler for ApiAdapter.

        :param path: URI path of resource
        :param request: HTTP request object passed from handler
        :return: ApiAdapterResponse container of data, content-type and status_code
        """
        logging.debug('GET on path %s from %s: method not implemented by %s',
                      path, request.remote_ip, self.name)
        response = "GET method not implemented by {}".format(self.name)
        return ApiAdapterResponse(response, status_code=400)

    def put(self, path, request):
        """Handle an HTTP PUT request.

        This method is an abstract implementation of the PUT request handler for ApiAdapter.

        :param path: URI path of resource
        :param request: HTTP request object passed from handler
        :return: ApiAdapterResponse container of data, content-type and status_code
        """
        logging.debug('PUT on path %s from %s: method not implemented by %s',
                      path, request.remote_ip, self.name)
        response = "PUT method not implemented by {}".format(self.name)
        return ApiAdapterResponse(response, status_code=400)

    def delete(self, path, request):
        """Handle an HTTP DELETE request.

        This method is an abstract implementation of the DELETE request handler for ApiAdapter.

        :param path: URI path of resource
        :param request: HTTP request object passed from handler
        :return: ApiAdapterResponse container of data, content-type and status_code
        """
        logging.debug('DELETE on path %s from %s: method not implemented by %s',
                      path, request.remote_ip, self.name)
        response = "DELETE method not implemented by {}".format(self.name)
        return ApiAdapterResponse(response, status_code=400)

    def cleanup(self):
        """Clean up adapter state.

        This is an abstract implementation of the cleanup mechanism provided to allow adapters
        to clean up their state (e.g. disconnect cleanly from the device being controlled, set
        some status message).
        """
        pass


class ApiAdapterResponse(object):
    """
    API adapter response object.

    This is a container class for responses returned by ApiAdapter method calls.
    It encapsulates the required attributes for all responses; data, content type and
    status code.
    """

    def __init__(self, data, content_type='text/plain', status_code=200):
        """Initialise the APiAdapterResponse object.

        :param data: data to return from data
        :param content_type: content type of response
        :param status_code: HTTP status code to return
        """
        self.data = data
        self.content_type = content_type
        self.status_code = status_code

    def set_content_type(self, content_type):
        """Set the content type for the adapter response.

        :param content_type: response content type
        """
        self.content_type = content_type

    def set_status_code(self, status_code):
        """Set the HTTP status code for the adapter response.

        :param status_code: HTTP status code
        """
        self.status_code = status_code


def request_types(*oargs):
    """
    Decorator method to define legal content types that adapter method will accept.

    This method compares the HTTP Content-Type header with a list of acceptable
    type. If there is a match, the adapter method is called accordingly, otherwise an
    HTTP 415 error response is returned.

    Typical usage would be, in an adapter, to decorate a verb method as follows:

    @request_types('application/json')
    def get(self, path, request)

    Note that both the request_types and response_types decorators can be applied to a
    method.

    :param oargs: a variable length list of acceptable content types
    :return: decorator context
    """
    def decorator(func):
        """Function decorator."""
        def wrapper(_self, path, request):
            """Inner method wrapper."""
            # Validate the Content-Type header in the request against allowed types
            if 'Content-Type' in request.headers:
                logging.debug("Request content type: %s", request.headers['Content-Type'])
                if request.headers['Content-Type'] not in oargs:
                    return ApiAdapterResponse(
                        'Request content type ({}) not supported'.format(
                            request.headers['Content-Type']), status_code=415)
            return func(_self, path, request)
        return wrapper
    return decorator


def response_types(*oargs, **okwargs):
    """
    Decorator method to define legal response types and a default for an adapter method.

    This method compares the HTTP request Accept header with a list of acceptable
    response types. If there is a match, the response type is set accordingly, otherwise
    an HTTP 406 error code is returned. A default type is also allowable, so if the request
    fails to specify a type (e.g. '*/*') then this will be used.

    Typical usage for this would be, in an adapter, to decorate a verb method as follows:

    @response_type('application/json', 'text/html', default='text/html')
    def get(self, path, request):
    <snip>

    to specify that the method has acceptable resonse types of JSON, HTML, defaulting to HTML

    :param oargs: a variable length list of  acceptable response types
    :param okwargs: keyword argument(s), allowing default type to be specified.
    :return: decorator context
    """
    def decorator(func):
        """Function decorator."""
        def wrapper(_self, path, request):
            """Inner function wrapper."""
            response_type = None

            # If Accept header is present, resolve the response type appropriately, otherwise
            # coerce to the default before calling the decorated function
            if 'Accept' in request.headers:

                if request.headers['Accept'] == '*/*':
                    if 'default' in okwargs:
                        response_type = okwargs['default']
                    else:
                        response_type = 'text/plain'
                else:
                    for accept_type in request.headers['Accept'].split(','):
                        accept_type = accept_type.split(';')[0]
                        if accept_type in oargs:
                            response_type = accept_type
                            break

                # If it was not possible to resolve a response type or there was not default
                # given, return an error code 406
                if response_type is None:
                    return ApiAdapterResponse(
                        "Requested content types not supported", status_code=406
                    )

            else:
                response_type = okwargs['default'] if 'default' in okwargs else 'text/plain'
                request.headers['Accept'] = response_type

            # Call the decorated function
            return func(_self, path, request)
        return wrapper
    return decorator

def wants_metadata(request):

    wants_metadata = False

    if "Accept" in request.headers:
        accept_elems = request.headers["Accept"].split(';')
        if len(accept_elems) > 1:
            for elem in accept_elems[1:]:
                if '=' in elem:
                    elem = elem.split('=')
                    if elem[0].strip() == "metadata":
                        wants_metadata = str(elem[1]).strip().lower() == 'true'

    return wants_metadata