"""Odin Server Utility Functions

This module implements utility methods for Odin Server.
"""
import sys
from tornado.escape import json_decode

PY3 = sys.version_info >= (3,)

if PY3:
    unicode = str


def decode_request_body(request):
    """Extract the body from a request.

    This might be decoded from json if specified by the request header.
    Otherwise, it will return the body as-is
    """

    try:
        body_type = request.headers["Content-Type"]
        if body_type == "application/json":
            body = json_decode(request.body)
        else:
            body = request.body
    except (TypeError):
        body = request.body
    return body


def convert_unicode_to_string(obj):
    """
    Convert all unicode parts of a dictionary or list to standard strings.

    This method will not handle special characters well due to the difference between uft-8
    and unicode.

    It is recursive, so if the object passed is a collection (dict or list) it will call
    itself for each object in the collection

    :param obj: the dictionary, list, or unicode string

    :return: the same data type as obj, but with unicode strings converted to python strings.
    """
    if PY3:
        # Python 3 strings ARE unicode, so no need to encode them
        return obj  # pragma: no cover
    if isinstance(obj, dict):
        # Obj is a dictionary. We need to recurse this method over each key and value
        return {convert_unicode_to_string(key): convert_unicode_to_string(value)
                for key, value in obj.items()}
    elif isinstance(obj, list):
        # Obj is a list. We need to recurse over each object in the list
        return [convert_unicode_to_string(element) for element in obj]
    elif isinstance(obj, unicode):
        return obj.encode("utf-8")
    # Obj is none of the above, just return it
    return obj


if PY3:
    import asyncio

    def wrap_result(result, is_async=True):
        """
        Conditionally wrap a result in an aysncio Future if being used in async code.

        This is to allow common functions for e.g. request validation, to be used in both
        async and sync code across python variants.

        param is_async: optional flag for if desired outcome is a result wrapped in a future

        :return: either the result or a Future wrapping the result
        """
        if is_async:
            f = asyncio.Future()
            f.set_result(result)
            return f
        else:
            return result
else:
    def wrap_result(result, is_async=True):
        """
        Conditionally wrap a result in an aysncio Future if being used in async code.

        This is to allow common functions for e.g. request validation, to be used in both
        async and sync code across python variants.

        param is_async: optional flag for if desired outcome is a result wrapped in a future

        :return: for this python 2 implementation, always returns just the result
        """
        return result
