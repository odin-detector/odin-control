import logging
import json

import tornado.web

def request_types(*oargs):
    def decorator(func):
        def wrapper(_self, *args, **kwargs):
            if 'Content-Type' in _self.request.headers:
                logging.debug("Request content type: %s", _self.request.headers['Content-Type'])
            func(_self, *args, **kwargs)
        return wrapper
    return decorator


def response_types(*oargs, **okwargs):
    """
    Decorator method to define legal response types and a default for a handler.

    This method compares the HTTP request Accept header with a list of acceptable
    response types. If there is a match, the response type is set accordingly, otherwise
    an HTTP 406 error code is returned. A default type is also allowable, so if the request
    fails to specify a type (e.g. '*/*') then this will be used.

    Typical usage for this would be, in a handler, to decorate a verb method as follows:

    @response_type('application/json', 'text/html', default='text/html')

    to specify that the

    :param oargs: an variable argument of acceptable response types
    :param okwargs: keyword argument(s), allowing default type to be specified.
    :return: decorator context
    """
    def decorator(func):
        """ Function decorator"""
        def wrapper(_self, *args, **kwargs):
            """Inner function wrapper"""

            _self.response_type = None

            # If Accept header is present, resolve the response type appropriately
            if 'Accept' in _self.request.headers:

                if _self.request.headers['Accept'] == '*/*':
                    if 'default' in okwargs:
                        _self.response_type = okwargs['default']
                    else:
                        _self.response_type = 'text/plain'
                else:
                    for accept_type in _self.request.headers['Accept'].split(','):
                        if accept_type in oargs:
                            _self.response_type = accept_type
                            break

                # If it was not possible to resolve a response type or there was not default
                # given, return an error code 406
                if _self.response_type is None:
                    _self.respond("Requested content types not supported", 406)
                    return

            else:
                _self.response_type = okwargs['default'] if 'default' in okwargs else 'text/plain'

            # Call the decorated function
            func(_self, *args, **kwargs)
        return wrapper
    return decorator


class Handler(tornado.web.RequestHandler):

    def __init__(self, application, request, **kwargs):

        super(Handler, self).__init__(application, request, **kwargs)
        self.response_type = None

    def respond(self, data, code=200):
        self.set_status(code)
        if self.response_type == 'application/json':
            if not isinstance(data, dict):
                data = json.dumps(data)

        self.write(data)
        if self.response_type is not None:
            self.set_header('Content-Type', self.response_type)
