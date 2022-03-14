"""parameter_tree.py - classes representing a sychronous parameter tree and accessor.

This module defines a parameter tree and accessor for use in synchronous API adapters, where
concurrency over blocking operations (e.g. to read/write the value of a parameter from hardware)
is not required.

Tim Nicholls, STFC Detector Systems Software Group.
"""
from odin.adapters.base_parameter_tree import (
    BaseParameterAccessor, BaseParameterTree, ParameterTreeError
)

__all__ = ['ParameterAccessor', 'ParameterTree', 'ParameterTreeError']


class ParameterAccessor(BaseParameterAccessor):
    """Synchronous container class representing accessor methods for a parameter.

    This class extends the base parameter accessor class to support synchronous set and get
    accessors for a parameter. Read-only and writeable parameters are supported, and the same
    metadata fields are implemented.
    """

    def __init__(self, path, getter=None, setter=None, **kwargs):
        """Initialise the ParameterAccessor instance.

        This constructor initialises the ParameterAccessor instance, storing the path of the
        parameter, its set/get accessors and setting metadata fields based on the the specified
        keyword arguments.

        :param path: path of the parameter within the tree
        :param getter: get method for the parameter, or a value if read-only constant
        :param setter: set method for the parameter
        :param kwargs: keyword argument list for metadata fields to be set; these must be from
                       the allow list specified in BaseParameterAccessor.allowed_metadata
        """
        # Initialise the superclass with the specified arguments
        super(ParameterAccessor, self).__init__(path, getter, setter, **kwargs)

        # Save the type of the parameter for type checking
        self._type = type(self.get())

        # Set the type metadata fields based on the resolved tyoe
        self.metadata["type"] = self._type.__name__


class ParameterTree(BaseParameterTree):
    """Class implementing a synchronous tree of parameters and their accessors.

    This lass implements an arbitrarily-structured, recursively-managed tree of parameters
    and the appropriate accessor methods that are used to read and write those parameters.
    """

    def __init__(self, tree, mutable=False):
        """Initialise the ParameterTree object.

        This constructor recursively initialises the ParameterTree object based on the specified
        arguments. The tree initialisation syntax follows that of the BaseParameterTree
        implementation.

        :param tree: dict representing the parameter tree
        :param mutable: Flag, setting the tree
        """
        # Set the accessor class used by this tree to ParameterAccessor
        self.accessor_cls = ParameterAccessor

        # Initialise the superclass with the speccified parameters
        super(ParameterTree, self).__init__(tree, mutable)
