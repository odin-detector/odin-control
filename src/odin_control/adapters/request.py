"""API adapter request classes for odin-control adapters.

This module defines the request container class used for internalcommunication between API adapters.

Tim Nicholls, STFC Detector Systems Software Group
"""


class ApiAdapterRequest(object):
    """API Adapter Request object.

    Emulate the HTTPServerRequest class passed as an argument to adapter HTTP
    verb methods (GET, PUT etc), for internal communication between adapters.
    """
    def __init__(self, data, content_type="application/vnd.odin-native",
                 accept="application/json", remote_ip="LOCAL"):
        """Initialize the Adapter Request body and headers.

        Create the header and body in the same way as in a HTTP Request.
        This means we can still use it in adapter HTTP verb methods
        """
        self.body = data
        self.content_type = content_type
        self.response_type = accept
        self.remote_ip = remote_ip
        self.headers = {
            "Content-Type": self.content_type,
            "Accept": self.response_type
        }

    def set_content_type(self, content_type):
        """Set the content type header for the request.

        The content type is filtered by the decorator "request_types". If
        it does not match the server will return a 415 error code.
        """
        self.content_type = content_type
        self.headers["Content-Type"] = content_type

    def set_response_type(self, response_type):
        """Set the type of response accepted by the request.

        The response type is filtered by the decorator "response_types". If
        it does not match the server will return a 406 error code.
        """
        self.response_type = response_type
        self.headers["Accept"] = response_type

    def set_remote_ip(self, ip):
        """Set the Remote IP of the request.

        This is only used in the event that an adapter has not implemented
        a GET or PUT request and is still using the base adapter class version
        of that method.
        """
        self.remote_ip = ip
