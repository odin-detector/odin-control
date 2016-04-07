import tornado.web
import importlib
import logging

def api_version(required_version):
    """
    Checks API version is correct, responds with a 400 error code if not
    """
    def decorator(func):
        def wrapper(_self, *args, **kwargs):
            # Extract version as first argument
            version = args[0]
            rem_args = args[1:]
            if version != unicode(required_version):
                _self.set_status(400)
                _self.write("API version {} is not supported\n".format(version))
            else:
                func(_self, *rem_args, **kwargs)
        return wrapper
    return decorator

class ApiDispatcher(object):

    def __init__(self):

        self.adapters = {}

    def register_adapter(self, path, adapter_name):

        (module_name, class_name) = adapter_name.rsplit('.', 1)
        logging.debug("Registering API adapter class {} from module {} with dispatcher".format(class_name, module_name))
        adapter_module = importlib.import_module(module_name)
        adapter_class  = getattr(adapter_module, class_name)

        self.adapters[path] = adapter_class()

class ApiHandler(tornado.web.RequestHandler):

    version = 0.1

    @api_version(version)
    def get(self, path):
        self.write("API GET on path {}\n".format(path))

    @api_version(version)
    def post(self, path):
        self.write("API POST on path {}\n".format(path))

ApiRoute = (r"/api/(.*?)/(.*)", ApiHandler)
