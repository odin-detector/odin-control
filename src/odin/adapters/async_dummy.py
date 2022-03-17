
"""Dummy asynchronous adapter classes for the ODIN server.

The AsyncDummyAdapter class implements a dummy asynchronous adapter for the ODIN server,
demonstrating the basic asymc adapter implementation and providing a loadable adapter for testing.

Tim Nicholls, STFC Detector Systems Software Group.
"""
import asyncio
import logging
import time
import concurrent.futures

from odin.adapters.adapter import ApiAdapterResponse, request_types, response_types
from odin.adapters.async_adapter import AsyncApiAdapter
from odin.adapters.async_parameter_tree import AsyncParameterTree
from odin.adapters.base_parameter_tree import ParameterTreeError
from odin.util import decode_request_body, run_in_executor


class AsyncDummyAdapter(AsyncApiAdapter):
    """Dummy asynchronous adapter class for the ODIN server.

    This dummy adapter implements basic asynchronous operation of an adapter, including use of an
    async parameter tree, and async GET and PUT methods. The parameter tree includes sync and async
    accessors, which simulate long-running tasks by sleeping, either using native async sleep or
    by sleeping in a thread pool executor. This shows that the calling server can remain responsive
    during long-running async tasks.
    """

    def __init__(self, **kwargs):
        """Intialize the AsyncDummy Adapter object.

        This constructor initializes the AsyncDummyAdapter object, including configuring an async
        parameter tree with accessors triggering simulated long-running task (sleep), the duration 
        and implemntation of which can be selected by configuration parameters.
        """
        super(AsyncDummyAdapter, self).__init__(**kwargs)

        # Parse the configuration options to determine the sleep duration and if we are wrapping
        # a synchronous sleep in a thread pool executor.
        self.async_sleep_duration = float(self.options.get('async_sleep_duration', 2.0))
        self.wrap_sync_sleep = bool(int(self.options.get('wrap_sync_sleep', 0)))

        sleep_mode_msg = 'sync thread pool executor' if self.wrap_sync_sleep else 'native async'
        logging.debug("Configuring async sleep task using {} with duration {} secs".format(
            sleep_mode_msg, self.async_sleep_duration
        ))

        # Initialise counters for the async and sync tasks and a trivial async read/write parameter
        self.sync_task_count = 0
        self.async_task_count = 0
        self.async_rw_param = 1234

        self.param_tree = AsyncParameterTree({
            'async_sleep_duration': (self.get_async_sleep_duration, None),
            'wrap_sync_sleep': (self.get_wrap_sync_sleep, None),
            'sync_task_count': (lambda: self.sync_task_count, None),
            'async_task_count': (lambda: self.async_task_count, None),
            'async_rw_param': (self.get_async_rw_param, self.set_async_rw_param),
        })

        # Create the thread pool executor
        self.executor = concurrent.futures.ThreadPoolExecutor()

    async def initialize(self, adapters):
        """Initalize the adapter.

        This dummy method demonstrates that async adapter initialisation can be performed
        asynchronously.

        :param adapters: list of adapters loaded into the server
        """
        logging.debug("AsyncDummyAdapter initialized with %d adapters", len(adapters))
        await asyncio.sleep(0)

    async def cleanup(self):
        """Clean up the adapter.

        This dummy method demonstrates that async adapter cleanup can be performed asynchronously.
        """
        logging.debug("AsyncDummyAdapter cleanup called")
        await asyncio.sleep(0)

    @response_types('application/json', default='application/json')
    async def get(self, path, request):
        """Handle an HTTP GET request.

        This method handles an HTTP GET request, returning a JSON response. The parameter tree
        data at the specified path is returned in the response. The underlying tree has a mix of
        sync and async parameter accessors, and GET requests simulate the concurrent operation of
        async adapters by sleeping for specified periods where appropriate.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        try:
            response = await self.param_tree.get(path)
            status_code = 200
        except ParameterTreeError as param_error:
            response = {'error': str(param_error)}
            status_code = 400

        logging.debug("GET on path %s : %s", path, response)
        content_type = 'application/json'

        return ApiAdapterResponse(response, content_type=content_type, status_code=status_code)

    @request_types('application/json', 'application/vnd.odin-native')
    @response_types('application/json', default='application/json')
    async def put(self, path, request):
        """Handle an HTTP PUT request.

        This method handles an HTTP PUT request, decoding the request and attempting to set values
        in the asynchronous parameter tree as appropriate.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        content_type = 'application/json'

        try:
            data = decode_request_body(request)
            await self.param_tree.set(path, data)
            response = await self.param_tree.get(path)
            status_code = 200
        except ParameterTreeError as param_error:
            response = {'error': str(param_error)}
            status_code = 400

        return ApiAdapterResponse(
            response, content_type=content_type, status_code=status_code
        )

    def sync_task(self):
        """Simulate a synchronous long-running task.

        This method simulates a long-running task by sleeping for the configured duration. It
        is made aysnchronous by wrapping it in a thread pool exector.
        """
        logging.debug("Starting simulated sync task")
        self.sync_task_count += 1
        time.sleep(self.async_sleep_duration)
        logging.debug("Finished simulated sync task")

    async def async_task(self):
        """Simulate a synchronous long-running task.

        This method simulates an async long-running task by performing an asyncio sleep for the
        configured duration.
        """
        logging.debug("Starting simulated async task")
        self.async_task_count += 1
        await asyncio.sleep(self.async_sleep_duration)
        logging.debug("Finished simulated async task")

    async def get_async_sleep_duration(self):
        """Simulate an async parameter access.

        This method demonstrates an asynchronous parameter access, return the current value of the
        async sleep duration parameter passed into the adapter as an option.
        """
        logging.debug("Entering async sleep duration get function")
        if self.wrap_sync_sleep:
            await run_in_executor(self.executor, self.sync_task)
        else:
            await asyncio.sleep(self.async_sleep_duration)

        logging.debug("Returning async sleep duration parameter: %f", self.async_sleep_duration)
        return self.async_sleep_duration

    def get_wrap_sync_sleep(self):
        """Simulate a sync parameter access.

        This method demonstrates a synchronous parameter access, returning the the current value
        of the wrap sync sleep parameter passed into the adapter as an option.
        """
        logging.debug("Getting wrap sync sleep flag: %s", str(self.wrap_sync_sleep))
        return self.wrap_sync_sleep

    async def get_async_rw_param(self):
        """Get the value of the async read/write parameter.

        This async method returns the current value of the async read/write parameter.

        :returns: current value of the async read/write parameter.
        """
        await asyncio.sleep(0)
        return self.async_rw_param

    async def set_async_rw_param(self, value):
        """Set the value of the async read/write parameter.

        This async updates returns the current value of the async read/write parameter.

        :param: new value to set parameter to
        """
        await asyncio.sleep(0)
        self.async_rw_param = value

