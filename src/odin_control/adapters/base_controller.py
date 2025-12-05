"""Base controller classes for odin-control adapters.

This module defines the base error class and abstract controller interface for odin control system
adapters.

Tim Nicholls, STFC Detector Systems Software Group
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseError(Exception):
    """Base exception class for adapter controllers.

    This exception class provides a common base for all adapter controller specific exceptions that
    may be raised during operation.
    """

    pass


class BaseController(ABC):
    """Abstract base class for adapter controllers.

    This class defines the interface that all adapter controllers must implementto provide
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
        """Initialize the controller with configuration options.

        :param options: Dictionary containing configuration options for the controller.
        """
        ...  # pragma: no cover

    def initialize(self, adapters: Dict[str, object]) -> None:
        """Initialize the controller with access to other adapters.

        This method is called after all adapters have been loaded and allows
        the controller to establish inter-adapter communication if needed.

        :param adapters: Dictionary mapping adapter names to adapter instances.
        """
        self.adapters = adapters

    def cleanup(self) -> None:
        """Clean up controller resources and state.

        This method should be implemented to properly clean up any resources,
        close connections, or perform other shutdown tasks when the controller
        is being stopped or destroyed.
        """
        ...

    @abstractmethod
    def get(self, path: str, with_metadata: bool = False) -> Dict[str, Any]:
        """Get data from the controller at the specified path.

        :param path: The path string identifying the resource to retrieve.
        :param with_metadata: Whether to include metadata in the response.

        :return: The requested data, format depends on controller implementation.
        """
        ...   # pragma: no cover

    def set(self, path: str, data: Dict[str, Any]) -> None:
        """Set data in the controller at the specified path.

        :param path: The path string identifying the resource to modify.
        :param data: The data to set at the specified path.
        """
        raise NotImplementedError()

    def create(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new resource at the specified path.

        :param path: The path string identifying where to create the resource.
        :param data: The data to use for creating the new resource.

        :return: Dictionary containing the created resource data.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        raise NotImplementedError()

    def delete(self, path: str) -> None:
        """Delete a resource at the specified path.

        :param path: The path string identifying the resource to delete.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        raise NotImplementedError()
