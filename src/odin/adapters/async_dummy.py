
"""Dummy asynchronous adapter classes for the ODIN server.

The AsyncDummyAdapter class implements a dummy asynchronous adapter for the ODIN server,
demonstrating the basic asymc adapter implementation and providing a loadable adapter for testing.

Tim Nicholls, STFC Detector Systems Software Group.
"""
import asyncio
import logging
import sys
import time
import concurrent.futures

from odin.adapters.adapter import ApiAdapterResponse, request_types, response_types
from odin.adapters.async_adapter import AsyncApiAdapter
from odin.util import decode_request_body

asyncio_get_running_loop = asyncio.get_running_loop \
    if sys.version_info >= (3, 7) else asyncio.get_event_loop


class AsyncDummyAdapter(AsyncApiAdapter):
    """Dummy asynchronous adapter class for the ODIN server.

    This dummy adapter implements basic async operation of an adapter, inclduing initialisation
    and HTTP verb methods GET and PUT. The verb moethods implement simulated long-running tasks
    by sleeping, either using native async sleep or by sleeping in a thread pool executor. This
    shows that the calling ODIN server can remain responsive during long-running async tasks.
    """

    def __init__(self, **kwargs):
        """Intialize the AsyncDummy Adapter object.

        This constructor initializes the AsyncDummyAdapter object, including configuring a simulated
        long-running task (sleep), the duration and implemtnation of which can be selected by
        configuration parameters.
        """
        super(AsyncDummyAdapter, self).__init__(**kwargs)

        # Parse the configuraiton options to determine the sleep duration and if we are wrapping
        # a synchronous sleep in a thread pool executor.
        self.async_sleep_duration = float(self.options.get('async_sleep_duration', 2.0))
        self.wrap_sync_sleep = bool(int(self.options.get('wrap_sync_sleep', 0)))

        sleep_mode_msg = 'sync thread pool executor' if self.wrap_sync_sleep else 'native async'
        logging.debug("Configuring async sleep task using {} with duration {} secs".format(
            sleep_mode_msg, self.async_sleep_duration
        ))

        # Create the thread pool executor
        self.executor = concurrent.futures.ThreadPoolExecutor()

    @response_types('application/json', default='application/json')
    async def get(self, path, request):
        """Handle an HTTP GET request.

        This method handles an HTTP GET request, returning a JSON response. To simulate a
        long-running async task that can be awaited, allowing the calling server to remain
        responsive, this method sleeps for the configured duration, either with a native
        async sleep or by wrapping a synchronous sleep in a thead pool executor.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        logging.info("In AsyncApiAdapter GET before sleep")

        if self.wrap_sync_sleep:
            loop = asyncio_get_running_loop()
            await loop.run_in_executor(self.executor, self.sync_task)
        else:
            await asyncio.sleep(self.async_sleep_duration)
        logging.info("In AsyncApiAdapter GET after sleep")

        return ApiAdapterResponse({'response': "AsyncDummyAdapter: GET on path {}".format(path)})

    @request_types('application/json', 'application/vnd.odin-native')
    @response_types('application/json', default='application/json')
    async def put(self, path, request):
        """Handle an API PUT request.

        This method handles an HTTP PUT request, returning a JSON response. To simulate a
        long-running async task that can be awaited, allowing the calling server to remain
        responsive, this method sleeps for the configured duration, either with a native
        async sleep or by wrapping a synchronous sleep in a thead pool executor.

        :param subsystem: subsystem element of URI, defining adapter to be called
        :param path: remaining URI path to be passed to adapter method
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        logging.info("In AsyncApiAdapter PUT before sleep")
        if self.wrap_sync_sleep:
            loop = asyncio_get_running_loop()
            await loop.run_in_executor(self.executor, self.sync_task)
        else:
            await asyncio.sleep(self.async_sleep_duration)
        logging.info("In AsyncApiAdapter PUT after sleep")

        body = decode_request_body(request)
        response = {'response': 'AsyncDummyAdapter: PUT on path {}'.format(path)}
        response.update(body)
        content_type = 'application/json'
        status_code = 200

        return ApiAdapterResponse(
            response, content_type=content_type, status_code=status_code
        )

    def sync_task(self):
        """Simulate a synchronous long-running task.

        This method simulates a long-running task by sleeping for the configured duration. It
        is made aysnchronous by wrapping it in a thread pool exector.
        """
        logging.debug("Starting simulated sync task")
        time.sleep(self.async_sleep_duration)
        logging.debug("Finished simulated sync task")
