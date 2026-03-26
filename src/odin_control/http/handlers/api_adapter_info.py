"""API adapter info handler module for odin-control.

This module implements the API adapter info handler. It allows clients to obtain information about
loaded API adapters through HTTP GET requests, returning the adapter information as JSON.

Tim Nicholls, STFC Detector Systems Software Group.
"""
from odin_control.http.handlers.cors_request import CorsRequestHandler


class ApiAdapterInfoHandler(CorsRequestHandler):
    """API adapter info handler to return information about loaded adapters.

    This request hander implements the GET verb to allow a call to the appropriate URI to return
    a JSON-encoded dictionary of information about the adapters loaded by the server.
    """

    def get(self, version=None):
        """Handle API adapter info GET requests.

        This handler returns a JSON-encoded dictionary of information about adapters loaded into the
        server.

        :param version: API version (or None if versioning not enabled)
        """
        # Validate the API version explicity - can't use the validate_api_request decorator here
        if version != self.route.api_version:
            self.set_status(400)
            self.write("API version {} is not supported".format(version))
            return

        # Validate the accept type requested is appropriate
        accept_types = self.request.headers.get('Accept', 'application/json').split(',')
        if '*/*' not in accept_types and 'application/json' not in accept_types:
            self.set_status(406)
            self.write('Request content types not supported')
            return

        # Build a dictionary of loaded adapter information
        adapter_info = {
            adapter_name: {
                'version': getattr(adapter, 'version', 'unknown'),
                "module": f"{adapter.__class__.__module__}.{adapter.__class__.__name__}",
            } for adapter_name, adapter in self.route.adapters.items()
        }

        # Return the loaded adapter information
        self.write({'adapters': adapter_info})
