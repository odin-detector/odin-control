import logging

from odin.adapters.adapter import ApiAdapter, ApiAdapterResponse, request_types, response_types


class IacDummyTargetAdapter(ApiAdapter):
    """Dummy adapter class for the Inter Adapter Communication changes.

    This dummy adapter impelements the basic operations of GET and PUT,
    and allows another adapter to interact with it via these methods.
    """

    def __init__(self, **kwargs):
        """Initialize the dummy target adapter.

        """

        super(IacDummyTargetAdapter, self).__init__(**kwargs)
        logging.debug("IAC Dummy Target Adapter Loaded")

    @response_types('application/json', default='application/json')
    def get(self, path, request):
        
        response = {"response": "IAC Adapter Target: GET on path {}".format(path)}
        content_type = 'application/json'
        status_code = 200

        return ApiAdapterResponse(response, content_type=content_type, status_code=status_code)

    @request_types('application/json', 'application/odin-native')
    @response_types('application/json', default='application/json')
    def put(self, path, request):
        response = {'response': 'IAC Adapter Target: PUT on path {}'.format(path)}
        content_type = 'application/json'
        status_code = 200

        logging.debug(response)

        return ApiAdapterResponse(response, content_type=content_type,
                                  status_code=status_code)
