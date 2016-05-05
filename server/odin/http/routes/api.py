import importlib
import logging
import json

import tornado.web

from odin.http.routes.route import Route
from odin.adapters.adapter import ApiAdapterResponse

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
                _self.respond(ApiAdapterResponse(
                    "API version {} is not supported".format(version),
                    status_code=400)
                )
            elif not _self.route.has_adapter(subsystem):
                _self.respond(ApiAdapterResponse(
                    "No API adapter registered for subsystem {}".format(subsystem),
                    status_code=400)
                )
            else:
                return func(_self, subsystem, *rem_args, **kwargs)
        return wrapper
    return decorator


class ApiError(Exception):
    pass


class ApiVersionHandler(tornado.web.RequestHandler):

    def get(self):
        if 'Accept' in self.request.headers:
            accept_type = self.request.headers['Accept']
            if accept_type == "*/*" or accept_type == 'application/json':
                self.set_status(200)
                self.write(json.dumps({'api_version' : _api_version}))
            else:
                self.set_status(406)
                self.write('Requested content types not supported')


class ApiHandler(tornado.web.RequestHandler):

    def initialize(self, route):
        self.route = route

    @validate_api_request(_api_version)
    def get(self, subsystem, path):
        response = self.route.adapter(subsystem).get(path, self.request)
        self.respond(response)

    @validate_api_request(_api_version)
    def put(self, subsystem, path):
        response = self.route.adapter(subsystem).put(path, self.request)
        self.respond(response)

    @validate_api_request(_api_version)
    def delete(self, subsystem, path):
        response = self.route.adapter(subsystem).delete(path, self.request)
        self.respond(response)

    def respond(self, response):

        self.set_status(response.status_code)
        self.set_header('Content-Type', response.content_type)

        data = response.data

        if response.content_type == 'application/json':
            if not isinstance(response.data, (str, dict)):
                raise ApiError(
                    'A response with content type application/json must have str or dict data'
                )

        self.write(data)


class ApiRoute(Route):

    def __init__(self):

        super(ApiRoute, self).__init__()

        # Define a default handler which can return the support API version
        self.add_handler((r"/api/?", ApiVersionHandler))

        # Define the handler for API calls. The expected URI syntax, which is
        # enforced by the validate_api_request decorator, is the following:
        #
        #    /api/<version>/<subsystem>/<action>....

        self.add_handler((r"/api/(.*?)/(.*?)/(.*)", ApiHandler, dict(route=self)))

        self.adapters = {}

    def register_adapter(self, adapter_config, fail_ok=True):

        """
        Registers an API adapter with the APIRoute object.

        Based on the adapter_config object passed in as an argument, this method attempts to
        load the specified module and create an instance of the adapter class to be used
        to handle requests to the API route on the appropriate path.

        :param adapter_config: AdapterConfig object for the adapter
        :param fail_ok: Allow the adapter import and registration to fail without raising an error
        """

        # Resolve the adapter module and class name from the dotted module path in the config object
        (module_name, class_name) = adapter_config.module.rsplit('.', 1)

        # Try to import the module, resolve the class in the module and create an instance of it
        try:
            adapter_module = importlib.import_module(module_name)
            adapter_class = getattr(adapter_module, class_name)
            self.adapters[adapter_config.name] = adapter_class(**adapter_config.options())

        except (ImportError, AttributeError) as e:
            logging.error(
                "Failed to register API adapter %s for path %s with dispatcher: %s",
                adapter_config.module, adapter_config.name, e)
            if not fail_ok:
                raise ApiError(e)
        else:
            logging.debug(
                "Registered API adapter class %s from module %s for path %s",
                class_name, module_name, adapter_config.name
            )

    def has_adapter(self, subsystem):

        return subsystem in self.adapters

    def adapter(self, subsystem):

        return self.adapters[subsystem]
