"""API adapter response classes for odin-control adapters.

This module defines the response container class used by API adapters to return data, content type
and status code information.

Tim Nicholls, STFC Detector Systems Software Group
"""


class ApiAdapterResponse(object):
    """API adapter response object.

    This is a container class for responses returned by ApiAdapter method calls.
    It encapsulates the required attributes for all responses; data, content type and
    status code.
    """

    def __init__(self, data, content_type="text/plain", status_code=200):
        """Initialise the APiAdapterResponse object.

        :param data: data to return from data
        :param content_type: content type of response
        :param status_code: HTTP status code to return
        """
        self.data = data
        self.content_type = content_type
        self.status_code = status_code

    def set_content_type(self, content_type):
        """Set the content type for the adapter response.

        :param content_type: response content type
        """
        self.content_type = content_type

    def set_status_code(self, status_code):
        """Set the HTTP status code for the adapter response.

        :param status_code: HTTP status code
        """
        self.status_code = status_code
