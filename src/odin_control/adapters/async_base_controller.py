"""Async base controller class for odin-control adapters.

This module defines the base error class and abstract controller interface for odin control system
adapters.

Tim Nicholls, STFC Detector Systems Software Group
"""
import asyncio
import inspect
from abc import ABC, abstractmethod
from typing import Any, Dict

from .base_controller import BaseError  # noqa: F401


class AsyncBaseController(ABC):
    """Abstract base class for asynchronous controllers.

    This class defines the interface that all async adapter controllers must implement to provide
    consistent behavior across different adapter types. Controllers handle the core logic and device
    communication for adapters.

    At a minimum, derived controller classes must implement the following methods:
    - __init__(options)
    - get(path, with_metadata=False)

    The following methods can be optionally implemented to provide additional functionality:
    - initialize(adapters)
    - cleanup()
    - set(path, data)
    - create(path, data)
    - delete(path)
    """

    @abstractmethod
    def __init__(self, options):
        """Initialize the asynchronous controller with configuration options.

        :param options: Dictionary containing configuration options for the controller.
        """
        ...  # pragma: no cover

    def __await__(self):
        """Make the controller awaitable to resolve async attributes."""
        async def closure():
            """Await all async attributes of the controller."""
            awaitable_attrs = [attr for attr in self.__dict__.values() if inspect.isawaitable(attr)]
            await asyncio.gather(*awaitable_attrs)
            return self

        return closure().__await__()

    async def initialize(self, adapters: Dict[str, object]) -> None:
        """Initialize the asynchronous controller with access to other adapters.

        This method is called after all adapters have been loaded and allows
        the controller to establish inter-adapter communication if needed.

        :param adapters: Dictionary mapping adapter names to adapter instances.
        """
        self.adapters = adapters

    async def cleanup(self) -> None:
        """Clean up controller resources and state.

        This method should be implemented to properly clean up any resources,
        close connections, or perform other shutdown tasks when the controller
        is being stopped or destroyed.
        """
        ...

    @abstractmethod
    async def get(self, path: str, with_metadata: bool = False) -> Dict[str, Any]:
        """Asynchronously get data from the controller at the specified path.

        :param path: The path string identifying the resource to retrieve.
        :param with_metadata: Whether to include metadata in the response.
        :return: A dictionary containing the requested data.
        """
        ...  # pragma: no cover

    async def set(self, path: str, data: Dict[str, Any]) -> None:
        """Asynchronously set data in the controller at the specified path.

        :param path: The path string identifying the resource to modify.
        :param data: A dictionary containing the data to set.
        """
        raise NotImplementedError()

    async def create(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Asynchronously create a new resource at the specified path.

        :param path: The path string identifying where to create the resource.
        :param data: A dictionary containing the data for the new resource.
        :return: A dictionary containing the created resource's data.
        """
        raise NotImplementedError()

    async def delete(self, path: str) -> None:
        """Asynchronously delete a resource at the specified path.

        :param path: The path string identifying the resource to delete.
        """
        raise NotImplementedError()
