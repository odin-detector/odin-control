"""
Drop-in replacement for absence of AsyncMock in python < 3.8.

Based on https://github.com/timsavage/asyncmock
"""

from unittest.mock import NonCallableMock, CallableMixin


class AsyncCallableMixin(CallableMixin):

    def __init__(_mock_self, not_async=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _mock_self.not_async = not_async
        _mock_self.aenter_return_value = _mock_self
        _mock_self._await_count = 0

    def __call__(_mock_self, *args, **kwargs):
        if _mock_self.not_async:
            _mock_self._mock_check_sig(*args, **kwargs)
            return _mock_self._mock_call(*args, **kwargs)
        else:
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
    Create a new `AsyncMock` object. `AsyncMock` several options that extends
    the behaviour of the basic `Mock` object:
    * `not_async`: This is a boolean flag used to indicate that when the mock
      is called it should not return a normal Mock instance to make the mock
      non-awaitable. If this flag is set the mock reverts to the default
      behaviour of a `Mock` instance.
    All other arguments are passed directly through to the underlying `Mock`
    object.
    """
