import pytest
import time
import concurrent.futures
import tornado.concurrent

from unittest.mock import Mock
import asyncio

from odin_control import util

class TestUtil():
    """Class to test utility functions in odin_control.util"""

    def test_decode_request_body(self):
        """Test that the body a a request is correctly decoded."""
        request = Mock
        request.headers = {'Content-Type': 'application/json'}
        request.body = '{"pi":2.56}'
        response = util.decode_request_body(request)
        assert response == {"pi": 2.56}

    def test_decode_request_body_not_json(self):
        """Test that the body of a native request is correctly decoded."""
        request = Mock
        request.headers = {'Content-Type': 'application/vnd.odin-native'}
        request.body = {"pi": 2.56}
        response = util.decode_request_body(request)
        assert response == request.body

    def test_decode_request_body_type_error(self):
        """Test that a body type mismatch returns the body unchanged."""
        request = Mock
        request.headers = {'Content-Type': 'application/json'}
        request.body = {"pi": 2.56}
        response = util.decode_request_body(request)
        assert response == request.body

    @pytest.mark.parametrize("is_async", [True, False], ids=["async", "sync"])
    def test_wrap_result(self, is_async):
        """Test that the wrap_result utility correctly wraps results in a future when needed."""
        result = 321
        wrapped_result = util.wrap_result(result, is_async)
        if is_async:
            assert isinstance(wrapped_result, asyncio.Future)
            assert wrapped_result.result() == result
        else:
            assert wrapped_result == result

    def test_run_in_executor(self):
        """Test that the run_in_executor utility can correctly nest asynchronous tasks."""
        # Container for task results modified by inner functions
        task_result = {
            'count': 0,
            'outer_completed': False,
            'inner_completed': False,
        }

        def nested_task(num_loops):
            """Simple task that loops and increments a counter before completing."""
            for _ in range(num_loops):
                time.sleep(0.01)
                task_result['count'] += 1
            task_result['inner_completed'] = True

        def outer_task(num_loops):
            """Outer task that launchas another task on an executor."""
            util.run_in_executor(executor, nested_task, num_loops)
            task_result['outer_completed'] = True

        executor = concurrent.futures.ThreadPoolExecutor()

        num_loops = 10
        future = util.run_in_executor(executor, outer_task, num_loops)

        wait_count = 0
        while not task_result['inner_completed'] and wait_count < 100:
            time.sleep(0.01)
            wait_count += 1

        assert isinstance(future, tornado.concurrent.Future)
        assert task_result['inner_completed'] is True
        assert task_result['count'] == num_loops
        assert task_result['outer_completed'] is True

class TestUtilAsync():

    @pytest.mark.asyncio
    async def test_wrap_result(self):
        """Test that the wrap_result utility correctly wraps results in a future when needed."""
        result = 321
        wrapped = util.wrap_result(result, True)
        await wrapped
        assert isinstance(wrapped, asyncio.Future)
        assert wrapped.result() == result

    @pytest.mark.asyncio
    async def test_wrap_async(self):
        """Test that the wrap_async fuction correctly wraps results in a future."""
        result = 987
        wrapped = util.wrap_async(result)
        await wrapped
        assert isinstance(wrapped, asyncio.Future)
        assert wrapped.result() == result

    @pytest.mark.asyncio
    async def test_run_in_executor(self):
        """
        Test that the run_in_executor utility runs a background task asynchronously and returns
        an awaitable future.
        """
        task_result = {
            'count': 0,
            'completed': False
        }

        def task_func(num_loops):
            """Simple task that loops and increments a counter before completing."""
            for _ in range(num_loops):
                time.sleep(0.01)
                task_result['count'] += 1
            task_result['completed'] = True

        executor = concurrent.futures.ThreadPoolExecutor()

        num_loops = 10
        await util.run_in_executor(executor, task_func, num_loops)

        wait_count = 0
        while not task_result['completed'] and wait_count < 100:
            asyncio.sleep(0.01)
            wait_count += 1

        assert task_result['completed']
        assert task_result['count'] == num_loops

    def test_run_async(self):

        async def async_increment(value):
            await asyncio.sleep(0)
            return value + 1

        value = 5
        result = util.run_async(async_increment, value)
        assert result == value + 1