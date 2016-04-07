import tornado.web
import importlib
import logging

def validate_api_request(required_version):
    """
    Checks API version is correct and that the subsystem is registered with the
    application dispatcher; responds with a 400 error if not
    """
    def decorator(func):
        def wrapper(_self, *args, **kwargs):
            # Extract version as first argument
            version = args[0]
            subsystem = args[1]
            rem_args = args[2:]
            if version != unicode(required_version):
                _self.respond("API version {} is not supported\n".format(version), 400)
            elif not subsystem in _self.dispatcher.adapters:
                _self.respond("No API adapter registered for subsystem {}\n".format(subsystem), 400)
            else:
                func(_self, subsystem, *rem_args, **kwargs)
        return wrapper
    return decorator

class ApiDispatcher(object):

    def __init__(self):

        self.adapters = {}
        ApiHandler.register_dispatcher(self)

    def register_adapter(self, path, adapter_name, fail_ok=True):

        (module_name, class_name) = adapter_name.rsplit('.', 1)
        try:
            adapter_module = importlib.import_module(module_name)
            adapter_class  = getattr(adapter_module, class_name)
            self.adapters[path] = adapter_class()
        except (ImportError, AttributeError) as e:
            logging.error("Failed to register API adapter {} for path {} with dispatcher: {}".format(adapter_name, path, e))
            if not fail_ok:
                raise ApiError(e)
        else:
            logging.debug("Registered API adapter class {} from module {} for path {}".format(class_name, module_name, path))

    def adapter(self, subsystem):

        return self.adapters[subsystem]

class ApiError(Exception):
    pass

class ApiHandler(tornado.web.RequestHandler):

    _api_version = 0.1

    @classmethod
    def register_dispatcher(cls, dispatcher):
        cls.dispatcher = dispatcher

    @validate_api_request(_api_version)
    def get(self, subsystem, path):
        self.write("API GET for subsystem {} on path {}\n".format(subsystem, path))

    @validate_api_request(_api_version)
    def post(self, subsystem, path):
        self.write("API POST for subsystem {} on path {}\n".format(subsystem, path))

    def respond(self, data, code=200):
        self.set_status(code)
        self.write(data)

"""
ApiRoute  - defines a URLspec for the API handler to be passed to the Tornado application.

The expected URL syntax, which is enforced by the validate_api_request decorator, is
the following:

   /api/<version>/<subsystem>/<action>....

"""
ApiRoute = (r"/api/(.*?)/(.*?)/(.*)", ApiHandler)
