import logging

from odin.adapters.adapter import ApiAdapter, ApiAdapterRequest, \
                                ApiAdapterResponse, request_types, response_types
from odin.util import decode_request_body


class IacDummyAdapter(ApiAdapter):
    """Dummy adapter class for the Inter Adapter Communication changes.

    This dummy adapter impelements the basic operations of GET and PUT,
    and allows another adapter to interact with it via these methods.
    """

    def __init__(self, **kwargs):
        """Initialize the dummy target adapter.

        Create the adapter using the base adapter class.
        Create an empty dictionary to store the references to other loaded adapters.
        """

        super(IacDummyAdapter, self).__init__(**kwargs)
        self.adapters = {}

        logging.debug("IAC Dummy Adapter Loaded")

    @response_types('application/json', default='application/json')
    def get(self, path, request):
        """Handle a HTTP GET Request

        Call the get method of each other adapter that is loaded and return the responses
        in a dictionary.
        """
        logging.debug("IAC DUMMY GET")
        response = {}
        request = ApiAdapterRequest(None, accept='application/json')
        for key, value in self.adapters.items():
            logging.debug("Calling Get of %s", key)
            response[key] = value.get(path=path, request=request).data
        logging.debug("Full response: %s", response)
        content_type = 'application/json'
        status_code = 200

        return ApiAdapterResponse(response, content_type=content_type, status_code=status_code)

    @request_types('application/json', 'application/vnd.odin-native')
    @response_types('application/json', default='application/json')
    def put(self, path, request):
        """Handle a HTTP PUT request.

        Calls the put method of each other adapter that has been loaded, and returns the responses
        in a dictionary.
        """
        logging.debug("IAC DUMMY PUT")
        body = decode_request_body(request)
        response = {}
        request = ApiAdapterRequest(body)

        for key, value in self.adapters.items():
            logging.debug("Calling Put of %s", key)
            response[key] = value.put(path="", request=request).data
        content_type = 'application/json'
        status_code = 200

        logging.debug(response)

        return ApiAdapterResponse(response, content_type=content_type,
                                  status_code=status_code)

    def initialize(self, adapters):
        """Initialize the adapter after it has been loaded.

        Receive a dictionary of all loaded adapters so that they may be accessed by this adapter.
        Remove itself from the dictionary so that it does not reference itself, as doing so
        could end with an endless recursive loop.
        """
        self.adapters = dict(adapters)
        for key, value in self.adapters.items():
            if value is self:
                del self.adapters[key]
                break

        logging.debug("Received following dict of Adapters: %s", self.adapters)
