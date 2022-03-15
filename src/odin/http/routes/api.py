"""API-related classes for the ODIN server.

This module implements a number of classes used by the ODIN server for routing and handling
API calls.

Tim Nicholls, STFC Application Engineering Group
"""

import importlib
import logging
import json

import tornado.web

from odin.http.routes.route import Route
from odin.util import PY3
from odin.http.handlers.base import ApiError, API_VERSION
if PY3:
    from odin.http.handlers.async_api import AsyncApiHandler as ApiHandler
    from odin.async_util import run_async
else:
    from odin.http.handlers.api import ApiHandler


class ApiVersionHandler(tornado.web.RequestHandler):
    """API version handler to allow client to resolve supported version.

    This request handler implements the GET verb to allow a call to the appropriate URI to return
    the supported API version as JSON.
    """

    def get(self):
        """Handle API version GET requests."""
        accept_types = self.request.headers.get('Accept', 'application/json').split(',')
        if "*/*" not in accept_types and 'application/json' not in accept_types:
            self.set_status(406)
            self.write('Requested content types not supported')
            return

        self.write(json.dumps({'api': API_VERSION}))


class ApiAdapterListHandler(tornado.web.RequestHandler):
    """API adapter list handler to return a list of loaded adapters.

    This request hander implements the GET verb to allow a call to the appropriate URI to return
    a JSON-encoded list of adapters loaded by the server.
    """

    def initialize(self, route):
        """Initialize the API adapter list handler.

        :param route: ApiRoute object calling the handler (allows adapters to be resolved)
        """
        self.route = route

    def get(self, version):
        """Handle API adapter list GET requests.

        This handler returns a JSON-encoded list of adapters loaded into the server.

        :param version: API version
        """
        # Validate the API version explicity - can't use the validate_api_request decorator here
        if version != str(API_VERSION):
            self.set_status(400)
            self.write("API version {} is not supported".format(version))
            return

        # Validate the accept type requested is appropriate
        accept_types = self.request.headers.get('Accept', 'application/json').split(',')
        if '*/*' not in accept_types and 'application/json' not in accept_types:
            self.set_status(406)
            self.write('Request content types not supported')
            return

        self.write({'adapters': [adapter for adapter in self.route.adapters]})


class ApiRoute(Route):
    """ApiRoute - API route object used to map handlers onto adapter for API calls."""

    def __init__(self):
        """Initialize the ApiRoute object."""
        super(ApiRoute, self).__init__()

        # Define a default handler which can return the supported API version
        self.add_handler((r"/api/?", ApiVersionHandler))

        # Define a handler which can return a list of loaded adapters
        self.add_handler((r'/api/(.*?)/adapters/?', ApiAdapterListHandler, dict(route=self)))

        # Define the handler for API calls. The expected URI syntax, which is
        # enforced by the validate_api_request decorator, is the following:
        #
        #    /api/<version>/<subsystem>/<action>....
        #
        # The second pattern allows an API adapter to be accessed with or without
        # a trailing slash for maximum compatibility
        self.add_handler((r"/api/(.*?)/(.*?)/(.*)", ApiHandler, dict(route=self)))
        self.add_handler((r"/api/(.*?)/(.*?)/?", ApiHandler, dict(route=self)))

        self.adapters = {}

    def register_adapter(self, adapter_config, fail_ok=True):
        """Register an API adapter with the APIRoute object.

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
            if PY3 and adapter_class.is_async:
                adapter = run_async(adapter_class, **adapter_config.options())
            else:
                adapter = adapter_class(**adapter_config.options())
            self.adapters[adapter_config.name] = adapter

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
        """Determine if ApiRoute object has adapter for subsystem.

        :param subsystem: subsystem to check for adapter
        :return: True of adapter present for subsystem
        """
        return subsystem in self.adapters

    def adapter(self, subsystem):
        """Return adapter for subsystem.

        :param subsystem: subsystem to return adapter for
        :return: adapter for subsystem
        """
        return self.adapters[subsystem]

    def cleanup_adapters(self):
        """Clean up state of registered adapters.

        This calls the cleanup method present in any registered adapters, allowing them to
        clean up their state (e.g. connected hardware) in a controlled fashion at shutdown.
        """
        for adapter_name, adapter in self.adapters.items():
            try:
                cleanup_method = getattr(adapter, 'cleanup')
                if PY3 and adapter.is_async:
                    run_async(cleanup_method)
                else:
                    cleanup_method()
            except AttributeError:
                logging.debug("Adapter %s has no cleanup method", adapter_name)

    def initialize_adapters(self):
        """Initialize all the adapters after they have been registered by the route.

        This calls the initialize method present in any registered adapters, passing
        the dictionary of listed adapters to each, for inter adapter communication.
        """
        for adapter_name, adapter in self.adapters.items():
            try:
                initialize_method = getattr(adapter, 'initialize')
                if PY3 and adapter.is_async:
                    run_async(initialize_method, self.adapters)
                else:
                    initialize_method(self.adapters)
            except AttributeError:
                logging.debug("Adapter %s has no initialize method", adapter_name)
