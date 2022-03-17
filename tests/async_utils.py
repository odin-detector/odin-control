"""
ijtiset
"""
import asyncio
from unittest.mock import NonCallableMock, CallableMixin

import pytest
import pytest_asyncio
try:
    asyncio_fixture_decorator = pytest_asyncio.fixture
except AttributeError:
    asyncio_fixture_decorator = pytest.fixture

class AwaitableTestFixture(object):
    """Class implementing an awaitable test fixture."""
    def __init__(self, awaitable_cls=None):
        self.awaitable_cls = awaitable_cls

    def __await__(self):

        async def closure():
            awaitables = [attr for attr in self.__dict__.values() if isinstance(
                attr,  self.awaitable_cls
            )]
            await asyncio.gather(*awaitables)
            return self
        
        return closure().__await__() 

class AsyncCallableMixin(CallableMixin):

    def __init__(_mock_self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _mock_self.aenter_return_value = _mock_self
        _mock_self._await_count = 0

    def __call__(_mock_self, *args, **kwargs):
        async def wrapper():
            _mock_self._await_count += 1
            _mock_self._mock_check_sig(*args, **kwargs)
            return _mock_self._mock_call(*args, **kwargs)
        return wrapper()

    async def __aenter__(_mock_self):
        return _mock_self.aenter_return_value

    async def __aexit__(_mock_self, exc_type, exc_val, exc_tb):
        pass

    def assert_awaited(_mock_self):
        if _mock_self._await_count == 0:
            raise AssertionError("Expected mock to have been awaited.")

    def assert_awaited_once(_mock_self):
        if _mock_self._await_count != 1:
            msg = (
                "Expected mock to have been awaited once. "
                "Awaited {} times.".format(_mock_self._await_count)
            )
            raise AssertionError(msg)

    @property
    def await_count(_mock_self):
        return _mock_self._await_count


class AsyncMock(AsyncCallableMixin, NonCallableMock):
    """
    Drop-in replacement for absence of AsyncMock in python < 3.8.

    Based on https://github.com/timsavage/asyncmock
    """
