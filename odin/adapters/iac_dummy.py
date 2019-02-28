import logging

from odin.adapters.adapter import ApiAdapter, ApiAdapterRequest, \
                                ApiAdapterResponse, request_types, response_types


class IacDummyAdapter(ApiAdapter):
    """Dummy adapter class for the Inter Adapter Communication changes.

    This dummy adapter impelements the basic operations of GET and PUT,
    and allows another adapter to interact with it via these methods.
    """

    def __init__(self, **kwargs):
        """Initialize the dummy target adapter.

        """

        super(IacDummyAdapter, self).__init__(**kwargs)
        self.adapters = {}
        logging.debug("IAC Dummy Adapter Loaded")

    @response_types('application/json', default='application/json')
    def get(self, path, request):
        logging.debug("IAC DUMMY GET")
        response = {}
        request = ApiAdapterRequest(None)
        request.set_response_type('application/json')
        for key, value in self.adapters.iteritems():
            logging.debug("Calling get of %s", key)
            logging.debug("Value Type: %s", type(value))
            response[key] = value.get(path="", request=request).data
        logging.debug("Full response: %s", response)
        content_type = 'application/json'
        status_code = 200

        return ApiAdapterResponse(response, content_type=content_type, status_code=status_code)

    @request_types('application/json', 'application/odin-native')
    @response_types('application/json', default='application/json')
    def put(self, path, request):
        response = {'response': 'IAC Adapter: PUT on path {}'.format(path)}
        content_type = 'application/json'
        status_code = 200

        logging.debug(response)

        return ApiAdapterResponse(response, content_type=content_type,
                                  status_code=status_code)

    def initialize(self, adapters):
        """Initialize the adapter after it has been loaded.
        
        Receive a dictionary of all loaded adapters so that they may be interrogated by this adapter
        """
        self.adapters = dict(adapters)
        for key, value in self.adapters.iteritems():
            if value is self:
                del self.adapters[key]
                break

        logging.debug("Received following dict of Adapters: %s", self.adapters)
        
