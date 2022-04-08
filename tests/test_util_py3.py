import sys
import pytest
import time
import concurrent.futures

import pytest_asyncio

from odin import util
from odin import async_util

if sys.version_info[0] < 3:
    pytest.skip("Skipping async tests", allow_module_level=True)

import asyncio


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
        wrapped = async_util.wrap_async(result)
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

        assert task_result['completed'] == True
        assert task_result['count'] == num_loops

    def test_run_async(self):

        async def async_increment(value):
            await asyncio.sleep(0)
            return value + 1

        value = 5
        result = async_util.run_async(async_increment, value)
        assert result == value + 1