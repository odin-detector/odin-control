import tornado.web
import importlib
import logging
import json

from odin.http.routes.route import Route
from odin.http.routes.handler import Handler, request_types, response_types

_api_version = 0.1

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
            if version != str(required_version):
                _self.respond("API version {} is not supported\n".format(version), 400)
            elif not _self.route.has_adapter(subsystem):
                _self.respond("No API adapter registered for subsystem {}\n".format(subsystem), 400)
            else:
                func(_self, subsystem, *rem_args, **kwargs)
        return wrapper
    return decorator


class ApiError(Exception):
    pass


class ApiVersionHandler(Handler):

    @response_types("application/json", default="application/json")
    def get(self):
        logging.debug("Response content-type: {}".format(self.response_type))
        self.respond({'api_version' : _api_version})


class ApiHandler(Handler):

    def initialize(self, route):
        self.route = route


    @validate_api_request(_api_version)
    def get(self, subsystem, path):
        (data, code) = self.route.adapter(subsystem).get(path)
        self.respond(data, code)

    @request_types("application/json")
    @validate_api_request(_api_version)
    def put(self, subsystem, path):
        (data, code) = self.route.adapter(subsystem).put(path)
        self.respond(data, code)

    @validate_api_request(_api_version)
    def delete(self, subsystem, path):
        (data, code) = self.route.adapter(subsystem).delete(path)
        self.respond(data, code)


class ApiRoute(Route):

    def __init__(self):

        # Define a default handler which can return the support API version
        self.add_handler((r"/api/?", ApiVersionHandler))

        # Define the handler for API calls. The expected URI syntax, which is
        # enforced by the validate_api_request decorator, is the following:
        #
        #    /api/<version>/<subsystem>/<action>....

        self.add_handler((r"/api/(.*?)/(.*?)/(.*)", ApiHandler, dict(route=self)))

        self.adapters = {}

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

    def has_adapter(self, subsystem):

        return subsystem in self.adapters

    def adapter(self, subsystem):

        return self.adapters[subsystem]
