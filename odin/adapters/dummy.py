""" Dummy adapter class for the ODIN server.

This class implements a dummy adapter for the ODIN server, demonstrating the
basic adapter implementation and providing a loadable adapter for testing

Tim Nicholls, STFC Application Engineering
"""
import logging
from concurrent import futures
import time
from tornado.ioloop import IOLoop
from tornado.concurrent import run_on_executor

from odin.adapters.adapter import ApiAdapter, ApiAdapterResponse, request_types, response_types


class DummyAdapter(ApiAdapter):
    """Dummy adapter class for the ODIN server.

    This dummy adapter implements the basic operation of an adapter including initialisation
    and HTTP verb methods (GET, PUT, DELETE) with various request and response types allowed.
    """

    # Thread executor used for background tasks
    executor = futures.ThreadPoolExecutor(max_workers=1)

    def __init__(self, **kwargs):
        """Initialize the DummyAdapter object.

        This constructor Initializes the DummyAdapter object, including launching a background
        task if enabled by the adapter options passed as arguments.

        :param kwargs: keyword arguments specifying options
        """
        super(DummyAdapter, self).__init__(**kwargs)

        # Set the background task counter to zero
        self.background_task_counter = 0

        # Launch the background task if enabled in options
        if self.options.get('background_task_enable', False):
            task_interval = float(
                self.options.get('background_task_interval', 1.0)
                )
            logging.debug(
                "Launching background task with interval %.2f secs", task_interval
            )
            self.background_task(task_interval)

        logging.debug('DummyAdapter loaded')

    @run_on_executor
    def background_task(self, task_interval):
        """Run the adapter background task.

        This simply increments the background counter and sleeps for the specified interval,
        before adding itself as a callback to the IOLoop instance to be called again.

        :param task_interval: time to sleep until task is run again
        """
        logging.debug("%s: background task running", self.name)
        self.background_task_counter += 1
        time.sleep(task_interval)
        IOLoop.instance().add_callback(self.background_task, task_interval)

    @response_types('application/json', default='application/json')
    def get(self, path, request):
        """Handle an HTTP GET request.

        This method handles an HTTP GET request, returning a JSON response. To facilitate
        testing of the background task, if the URI path is set appropriately, the task
        counter is returned in the JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        if path == 'background_task_count':
            response = {'response': {
                'background_task_count': self.background_task_counter}
            }
        else:
            response = {'response': 'DummyAdapter: GET on path {}'.format(path)}

        content_type = 'application/json'
        status_code = 200

        logging.debug(response)

        return ApiAdapterResponse(response, content_type=content_type,
                                  status_code=status_code)

    @request_types('application/json')
    @response_types('application/json', default='application/json')
    def put(self, path, request):
        """Handle an HTTP PUT request.

        This method handles an HTTP PUT request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        response = {'response': 'DummyAdapter: PUT on path {}'.format(path)}
        content_type = 'application/json'
        status_code = 200

        logging.debug(response)

        return ApiAdapterResponse(response, content_type=content_type,
                                  status_code=status_code)

    def delete(self, path, request):
        """Handle an HTTP DELETE request.

        This method handles an HTTP DELETE request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        response = 'DummyAdapter: DELETE on path {}'.format(path)
        status_code = 200

        logging.debug(response)

        return ApiAdapterResponse(response, status_code=status_code)

    def cleanup(self):
        """Clean up the state of the adapter.

        This method cleans up the state of the adapter, which in this case is
        trivially setting the background task counter back to zero for test
        purposes.
        """
        logging.debug("DummyAdapter cleanup: resetting background test counter")
        self.background_task_counter = 0
