"""Utility functions for odin-control.

This module implements utility methods for odin-control.
"""
import asyncio

from tornado.escape import json_decode
from tornado.ioloop import IOLoop


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
    # Try to get the current asyncio event loop, otherwise create a new one
    get_async_event_loop()

    # Run the function in the specified executor, handling tornado version 4 where there was no
    # run_in_executor implementation
    future = IOLoop.current().run_in_executor(executor, func, *args)

    return future

def get_async_event_loop():
    """Get the asyncio event loop.

    This function obtains and returns the current asyncio event loop. If no loop is present, a new
    one is created and set as the event loop.

    :return: an asyncio event loop
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop


def run_async(func, *args, **kwargs):
    """Run an async function synchronously in an event loop.

    This function can be used to run an async function synchronously, i.e. without the need for an
    await() call. The function is run on an asyncio event loop and the result is returned.

    :param func: async function to run
    :param args: positional arguments to function
    :param kwargs:: keyword arguments to function
    :return: result of function
    """
    loop = get_async_event_loop()
    result = loop.run_until_complete(func(*args, **kwargs))
    return result

