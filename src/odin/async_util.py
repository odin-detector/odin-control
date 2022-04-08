"""Odin server asyncio utility functions.

This module implements asyncio-based utility functions needed in odin-control when using
asynchronous adapters.

Tim Nicholls, STFC Detector System Software Group.
"""
import asyncio


def wrap_async(object):
    """Wrap an object in an async future.

    This function wraps an object in an async future and is called from wrap_result when
    async objects are wrapped in python 3. A future is created, its result set to the
    object passed in, and returned to the caller.

    :param object: object to wrap in a future
    :return: a Future with object as its result
    """
    future = asyncio.Future()
    future.set_result(object)
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
