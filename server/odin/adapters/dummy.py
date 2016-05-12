import logging
from concurrent import futures
import time
from tornado.ioloop import IOLoop
from tornado.concurrent import run_on_executor

from odin.adapters.adapter import ApiAdapter, ApiAdapterResponse, request_types, response_types

class DummyAdapter(ApiAdapter):

    executor = futures.ThreadPoolExecutor(max_workers=1)

    def __init__(self, **kwargs):

        super(DummyAdapter, self).__init__(**kwargs)

        self.background_task_counter = 0

        # Launch the background task if enabled in options
        if self.options.get('background_task_enable', False):
            task_interval = float(
                self.options.get('background_task_interval', 1.0)
                )
            logging.debug(
                "Launching background task with interval %.2f secs" % task_interval
            )
            self.background_task(task_interval)

        logging.debug('DummyAdapter loaded')

    @run_on_executor
    def background_task(self, task_interval):
        logging.debug("%s: background task running", self.name)
        self.background_task_counter += 1
        time.sleep(task_interval)
        IOLoop.instance().add_callback(self.background_task, task_interval)

    @response_types('application/json', default='application/json')
    def get(self, path, request):

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

        response = {'response' : 'DummyAdapter: PUT on path {}'.format(path)}
        content_type = 'application/json'
        status_code = 200

        logging.debug(response)

        return ApiAdapterResponse(response, content_type=content_type,
                                  status_code=status_code)

    def delete(self, path, request):

        response = 'DummyAdapter: DELETE on path {}'.format(path)
        status_code = 200

        logging.debug(response)

        return ApiAdapterResponse(response, status_code=status_code)
