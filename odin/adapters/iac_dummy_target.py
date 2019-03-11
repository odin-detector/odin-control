import logging

from odin.adapters.adapter import ApiAdapter, ApiAdapterResponse, request_types, response_types
from odin.util import decode_request_body
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError


class IacDummyTargetAdapter(ApiAdapter):
    """Dummy adapter class for the Inter Adapter Communication changes.

    This dummy adapter impelements the basic operations of GET and PUT,
    and allows another adapter to interact with it via these methods.
    """

    def __init__(self, **kwargs):
        """Initialize the dummy target adapter.

        Create a paramter tree based off the options given by the configuration.
        """

        super(IacDummyTargetAdapter, self).__init__(**kwargs)
        self.param_tree = ParameterTree(self.options)
        logging.debug("IAC Dummy Target Adapter Loaded")

    @response_types('application/json', default='application/json')
    def get(self, path, request):
        """Handle a HTTP GET Request.

        Return the value requested from the parameter tree.
        If no path was specified, return the entire parameter tree.
        """
        try:
            response = self.param_tree.get(path)
            status_code = 200
        except ParameterTreeError as e:
            response = {'error': str(e)}
            status_code = 400

        content_type = 'application/json'
        return ApiAdapterResponse(response, content_type=content_type, status_code=status_code)

    @request_types('application/json', 'application/vnd.odin-native')
    @response_types('application/json', default='application/json')
    def put(self, path, request):
        """Handle a HTTP PUT Request.

        Return a dictionary containing the data from the PUT request.
        As this is a dummy adapter this does not actually modify the parameter tree.
        """
        data = decode_request_body(request)
        logging.debug("Data: %s, type: %s", data, type(data))
        response = {'response': 'IAC Adapter Target: PUT on path {}'.format(path)}
        response["data"] = data
        content_type = 'application/json'
        status_code = 200

        logging.debug(response)

        return ApiAdapterResponse(response, content_type=content_type,
                                  status_code=status_code)
