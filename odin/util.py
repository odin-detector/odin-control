"""Odin Server Utility Functions

This module implements utility methods for Odin Server.
"""
import sys
from tornado.escape import json_decode

PY3 = sys.version_info >= (3,)


def decode_request_body(request):
    """Extract the body from a request

    Returns the body from the
    request. This may be decoded from json if required.
    """

    try:
        body_type = request.headers["Content-Type"]
        if body_type == 'application/json':
            body = json_decode(request.body)
        else:
            body = request.body
    except (TypeError, ValueError):
        body = request.body
    return body


def convert_to_string(obj):
    """
    Convert all unicode parts of a dictionary or list to standard strings.

    This method may not handle special characters well due to the difference between uft-8 and unicode.
    :param obj: the dictionary, list, or unicode string
    :return: the same data type as obj, but with unicode strings converted to python strings.
    """
    if PY3:
        return obj  # Python 3 strings ARE unicode, so no need to encode them
    if isinstance(obj, dict):
        return {convert_to_string(key): convert_to_string(value)
                for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_string(element) for element in obj]
    elif isinstance(obj, unicode):
        return obj.encode('utf-8')

    return obj
