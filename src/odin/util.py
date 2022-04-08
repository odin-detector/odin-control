"""Odin Server Utility Functions

This module implements utility methods for Odin Server.
"""
import sys

from tornado import version_info
from tornado.escape import json_decode
from tornado.ioloop import IOLoop

PY3 = sys.version_info >= (3,)

if PY3:
    from odin.async_util import get_async_event_loop, wrap_async
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


def wrap_result(result, is_async=True):
    """
    Conditionally wrap a result in an aysncio Future if being used in async code on python 3.

    This is to allow common functions for e.g. request validation, to be used in both
    async and sync code across python variants.

    :param is_async: optional flag for if desired outcome is a result wrapped in a future

    :return: either the result or a Future wrapping the result
    """
    if is_async and PY3:
        return wrap_async(result)
    else:
        return result


def run_in_executor(executor, func, *args):
    """
    Run a function asynchronously in an executor.

    This method extends the behaviour of Tornado IOLoop equivalent to allow nested task execution
    without having to modify the underlying asyncio loop creation policy on python 3. If the
    current execution context does not have a valid IO loop, a new one will be created and used.
    The method returns a tornado Future instance, allowing it to be awaited in an async method where
    applicable.

    :param executor: a concurrent.futures.Executor instance to run the task in
    :param func: the function to execute
    :param arg: list of arguments to pass to the function

    :return: a Future wrapping the task
    """
    # In python 3, try to get the current asyncio event loop, otherwise create a new one
    if PY3:
        get_async_event_loop()

    # Run the function in the specified executor, handling tornado version 4 where there was no
    # run_in_executor implementation
    if version_info[0] <= 4:
        future = executor.submit(func, *args)
    else:
        future = IOLoop.current().run_in_executor(executor, func, *args)

    return future
