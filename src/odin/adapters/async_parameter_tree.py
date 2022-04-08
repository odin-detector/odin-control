"""async_parameter_tree.py - classes representing an asychronous parameter tree and accessor.

This module defines a parameter tree and accessor for use in asynchronous API adapters, where
concurrency over blocking operations (e.g. to read/write the value of a parameter from hardware)
is required.

Tim Nicholls, STFC Detector Systems Software Group.
"""

import asyncio

from odin.adapters.base_parameter_tree import (
    BaseParameterAccessor, BaseParameterTree, ParameterTreeError
)

__all__ = ['AsyncParameterAccessor', 'AsyncParameterTree', 'ParameterTreeError']

# if sys.version_info < (3,7):
#     async_create_task = asyncio.ensure_future
# else:
#     async_create_task = asyncio.create_task
try:
    async_create_task = asyncio.create_task
except AttributeError:
    async_create_task = asyncio.ensure_future
    
class AsyncParameterAccessor(BaseParameterAccessor):
    """Asynchronous container class representing accessor methods for a parameter.

    This class extends the base parameter accessor class to support asynchronous set and get
    accessors for a parameter. Read-only and writeable parameters are supported, and the same
    metadata fields are implemented.

    Note that the instantiation of objects of this class MUST be awaited to allow the getter
    function to evaluate and record the parameter type in the metadata, e.g.

    accessor = await AsyncParameterAccessor(....)

    Accessors instantiated during the intialisation of an AsyncParameterTree will automatically be
    collected and awaited by the tree itself.
    """

    def __init__(self, path, getter=None, setter=None, **kwargs):
        """Initialise the AsyncParameterAccessor instance.

        This constructor initialises the AsyncParameterAccessor instance, storing the path of the
        parameter, its set/get accessors and setting metadata fields based on the the specified
        keyword arguments.

        :param path: path of the parameter within the tree
        :param getter: get method for the parameter, or a value if read-only constant
        :param setter: set method for the parameter
        :param kwargs: keyword argument list for metadata fields to be set; these must be from
                       the allow list specified in BaseParameterAccessor.allowed_metadata
        """
        # Initialise the superclass with the specified arguments
        super(AsyncParameterAccessor, self).__init__(path, getter, setter, **kwargs)

    def __await__(self):
        """Make AsyncParameterAccessor objects awaitable.

        This magic method makes the instantiation of AsyncParameterAccessor objects awaitable. This
        is required since instantiation must call the specified get() method, which is itself async,
        in order to resolve the type of the parameter and store that in the metadata. This cannot be
        done directly in the constructor.

        :returns: an awaitable future
        """
        async def closure():
            """Resolve the parameter type in an async closure."""
            self._type = type(await self.get())
            self.metadata["type"] = self._type.__name__
            return self

        return closure().__await__()

    @staticmethod
    async def resolve_coroutine(value):
        """Resolve a coroutine and return its value.

        This static convenience method allows an accessor to resolve the output of its getter/setter
        functions to avalue if an async coroutine is returned.

        :param value: value or coroutine to resolve
        :returns: resolved value
        """
        if value and asyncio.iscoroutine(value):
            value = await value

        return value

    async def get(self, with_metadata=False):
        """Get the value of the parameter.

        This async method returns the value of the parameter, or the value returned by the accessor
        getter, if one is defined (i.e. is callable). If the getter is itself async, the value is
        resolved by awaiting the returned coroutine. If the with_metadata argument is true, the
        value is returned in a dictionary including all metadata for the parameter.

        :param with_metadata: include metadata in the response when set to True
        :returns value of the parameter
        """
        # Call the superclass get method
        value = super(AsyncParameterAccessor, self).get(with_metadata)

        # Resolve and await the returned value, either into the metadata-populated dict or directly
        # as the returned value
        if with_metadata:
            value["value"] = await(self.resolve_coroutine(value["value"]))
        else:
            value = await self.resolve_coroutine(value)

        return value

    async def set(self, value):
        """Set the value of the parameter.

        This async method sets the value of the parameter by calling the set accessor
        if defined and callable. The result is awaited if a coroutine is returned.

        :param value: value to set
        """
        await self.resolve_coroutine(super(AsyncParameterAccessor, self).set(value))


class AsyncParameterTree(BaseParameterTree):
    """Class implementing an asynchronous tree of parameters and their accessors.

    This async class implements an arbitrarily-structured, recursively-managed tree of parameters
    and the appropriate accessor methods that are used to read and write those parameters.

    Note that the instantiation of an AsyncParameterTree MUST be awaited by calling code to allow
    the type and intial value of each parameter to be resolved, e.g.:

    tree = await AsyncParameterTree(...)
    """

    def __init__(self, tree, mutable=False):
        """Initialise the AsyncParameterTree object.

        This constructor recursively initialises the AsyncParameterTree object based on the
        specified arguments. The tree initialisation syntax follows that of the BaseParameterTree
        implementation.

        :param tree: dict representing the parameter tree
        :param mutable: Flag, setting the tree
        """
        # Set the accessor class used by this tree to AsyncParameterAccessor
        self.accessor_cls = AsyncParameterAccessor

        # Initialise the superclass with the speccified parameters
        super(AsyncParameterTree, self).__init__(tree, mutable)

    def __await__(self):
        """Make AsyncParameterTree objects awaitable.

        This magic method makes the instantiation of AsyncParameterTree objects awaitable. This
        is required since the underlying accessor objects must also be awaited at initialisation
        to resolve their type and intial values. This is achieved by traversing the parameter tree
        and gathering all awaitable accessor instances and awaiting them.
        """
        def get_awaitable_params(node):
            """Traverse the parameter tree and build a list of awaitable accessors."""
            awaitable_params = []
            if (isinstance(node, dict)):
                for val in node.values():
                    if isinstance(val, self.accessor_cls):
                        awaitable_params.append(val)
                    else:
                        awaitable_params.extend(get_awaitable_params(val))
            return awaitable_params

        async def closure():
            """Resolve the parameter tree accessor types in an async closure."""
            await asyncio.gather(*get_awaitable_params(self.tree))
            return self

        return closure().__await__()

    async def get(self, path, with_metadata=False):
        """Get the values of parameters in a tree.

        This async method returns the values at and below a specified path in the parameter tree.
        This is done by recursively populating the tree with the current values of parameters,
        returning the result as a dictionary.

        :param path: path in tree to get parameter values for
        :param with_metadata: include metadata in the response when set to True
        :returns: dict of parameter tree at the specified path
        """
        value = super(AsyncParameterTree, self).get(path, with_metadata)

        async def resolve_value(value):
            """Recursively resolve the values of the parameters.

            This inner method recursively decends through the tree of parameters being returned by
            the get() call, awaiting any async getter methods. These are done sequentially to allow
            the values to be resolved in-place within the tree.
            """
            if isinstance(value, dict):
                for (k, v) in value.items():
                    if asyncio.iscoroutine(v):
                        value[k] = await v
                    else:
                        await resolve_value(v)

        # Resolve values of parameters in the tree
        await resolve_value(value)
        return value

    async def set(self, path, data):
        """Set the values of the parameters in a tree.

        This async method sets the values of parameters in a tree, based on the data passed to it
        as a nested dictionary of parameter and value pairs. The updated parameters are merged
        into the existing tree recursively.

        :param path: path to set parameters for in the tree
        :param data: nested dictionary representing values to update at the path
        """
        # Create an empty list of awaitable parameters
        self.awaitable_params = []

        # Call the superclass set method with the specified parameters
        super(AsyncParameterTree, self).set(path, data)

        # Await any async set methods in the modified parameters
        await asyncio.gather(*self.awaitable_params)

    def _set_node(self, node, data):
        """Set the value of a node to the specified data.

        This method sets a specified node to the data supplied. If the setter function for the node
        is async, it is added to the list of parameters to be awaited by the set() method.

        :param node: tree node to set value of
        :param data: data to node value to
        """
        response = node.set(data)
        if asyncio.iscoroutine(response):
            self.awaitable_params.append(async_create_task(response))
