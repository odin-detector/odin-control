import tornado.web
import logging
import json

def request_types(*oargs):
    def decorator(func):
        def wrapper(_self, *args, **kwargs):
            if 'Content-Type' in _self.request.headers:
                logging.debug("Request content type: {}".format(_self.request.headers['Content-Type']))
            func(_self, *args, **kwargs)
        return wrapper
    return decorator

def response_types(*oargs, **okwargs):
    def decorator(func):
        def wrapper(_self, *args, **kwargs):
            _self.response_type = None
            if 'Accept' in _self.request.headers:
                for accept_type in _self.request.headers['Accept'].split(','):
                    if accept_type in oargs:
                        _self.response_type = accept_type
                        break
                if _self.response_type == None:
                    _self.respond("Requested content types not supported", 406)
                    return
            else:
                _self.response_type = okwargs['default'] if 'default' in okwargs else 'text/plain'
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
        if self.response_type != None:
            self.set_header('Content-Type', self.response_type)
