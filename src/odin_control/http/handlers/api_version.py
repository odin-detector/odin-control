import json

from tornado.web import RequestHandler

from .api import API_VERSION

class ApiVersionHandler(RequestHandler):
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