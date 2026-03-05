"""Utility functions and decorators for odin-control API adapters.

This module provides common decorators and utility functions used by adapters for request/response
type validation and controller management.

Tim Nicholls, STFC Detector System Software Group
"""
import asyncio

from odin_control.adapters.response import ApiAdapterResponse


def wrap_result(result, is_async=True):
    """Conditionally wrap a result in an aysncio Future if being used in async code.

    This method allows common functions for e.g. request validation, to be used in both
    async and sync adapters.

    :param result: the result to potentially wrap
    :param is_async: optional flag for if desired outcome is a result wrapped in a future

    :return: either the result or a Future wrapping the result
    """
    if is_async:
        future = asyncio.Future()
        future.set_result(result)
        return future
    else:
        return result


def request_types(*oargs):
    """Ensure that a request has a legal content types that an adapter method will accept.

    This decorator method compares the HTTP Content-Type header with a list of acceptable
    types. If there is a match, the adapter method is called accordingly, otherwise an
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
                if request.headers['Content-Type'] not in oargs:
                    response = ApiAdapterResponse(
                        f'Request content type ({request.headers["Content-Type"]}) not supported',
                        status_code=415)
                    return wrap_result(response, _self.is_async)
            return func(_self, path, request)
        return wrapper
    return decorator


def response_types(*oargs, **okwargs):
    """Ensure that a request wants legal response types for an adapter method.

    This decorator method compares the HTTP Accept header with a list of acceptable
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
                    response = ApiAdapterResponse(
                        "Requested content types not supported", status_code=406
                    )
                    return wrap_result(response, _self.is_async)
            else:
                response_type = okwargs['default'] if 'default' in okwargs else 'text/plain'
                request.headers['Accept'] = response_type

            # Call the decorated function
            return func(_self, path, request)
        return wrapper
    return decorator


def require_controller(func):
    """Ensure the adapter has a valid controller before executing HTTP methods.

    This decorator checks if the adapter instance has a valid controller object
    in self.controller. If not, it returns a JSON error response with status 405.

    :param func: The HTTP method function to decorate
    :return: Decorated function that validates controller presence
    """
    def wrapper(_self, path, request):
        """Wrapper function that validates controller presence."""
        if not _self.controller:
            response = ApiAdapterResponse(
                { "error": f"Adapter {_self.name} has no controller configured" },
                content_type="application/json",
                status_code=405
            )
            return wrap_result(response, _self.is_async)
        return func(_self, path, request)
    return wrapper


def wants_metadata(request):
    """Determine if a client request wants metadata to be included in the response.

    This method checks to see if an incoming request has an Accept header with
    the 'metadata=true' qualifier attached to the MIME-type.

    :param request: HTTPServerRequest or equivalent from client
    :returns: boolean, True if metadata is requested.
    """
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
