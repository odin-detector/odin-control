"""Cross-Origin Resource Sharing (CORS) handler for odin-control.

This module implements a simple handler to respond to CORS preflight requests from clients,
allowing CORS requests to be made to API handlers.

Tim Nicholls, STFC Detector Systems Software Group.
"""
from tornado.web import RequestHandler


class CorsRequestHandler(RequestHandler):
    """Handler to respond to CORS requests.

    This handler responds to HTTP OPTIONS requests and sets the appropriate headers to allow CORS
    requests from the specified origin. This class is intended to be used as a base class for API
    handlers to allow CORS requests to be made to API endpoints.
    """

    def __init__(self, *args, **kwargs):
        """Construct the CorsRequestHandler object.

        This method constructs the CorsRequestHandler object, calling the superclass constructor and
        setting the route object to None.
        """
        self.route = None
        super().__init__(*args, **kwargs)

    def initialize(self, route, enable_cors, cors_origin):
        """Initialize the CorsRequestHandler object.

        :param route: ApiRoute object calling the handler (allows adapters to be resolved)
        :param enable_cors: enable CORS support by setting appropriate headers
        :param cors_origin: allowed origin for CORS requests
        """
        self.route = route
        if enable_cors:
            self.set_header("Access-Control-Allow-Origin", cors_origin)
            self.set_header("Access-Control-Allow-Headers", "x-requested-with,content-type")
            self.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")

    def options(self, *_):
        """Handle an OPTIONS request.

        This method handles an OPTION request and is provided to allow browser clients to employ
        CORS preflight requests to determine if non-simple requests are allowed.

        :param _: unused arguments passed to the method by the URI matching in the handler
        """
        # Set status to indicate successful request with no content returned
        self.set_status(204)
