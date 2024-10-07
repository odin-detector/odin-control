"""base_parameter_tree.py - base classes representing a tree of parameters and accessors.

This module implements an arbitrarily-structured, recursively-managed tree of parameters and
the appropriate accessor methods that are used to read and write those parameters. Its
particular use is in the definition of a tree of parameters for an API adapter and help
interfacing of those to the underlying device or object. These base classes are not intended to be
used directly, but form the basis for concrete synchronous and asynchronous implementations.

James Hogge, Tim Nicholls, STFC Application Engineering Group.
"""


class ParameterTreeError(Exception):
    """Simple error class for raising parameter tree parameter tree exceptions."""

    pass


class BaseParameterAccessor(object):
    """Base container class representing accessor methods for a parameter.

    This base class implements a parameter accessor, provding set and get methods
    for parameters requiring calls to access them, or simply returning the
    appropriate value if the parameter is a read-only constant. Parameter accessors also
    contain metadata fields controlling access to and providing information about the parameter.

    Valid specifiable metadata fields are:
    min : minimum allowed value for parameter
    max : maxmium allowed value for parameter
    allowed_values: list of allowed values for parameter
    name : readable parameter name
    description: longer description of parameter
    units: parameter units
    display_precision: number of decimal places to display for e.g. float types

    The class also maintains the following automatically-populated metadata fields:
    type: parameter type
    writeable: is the parameter writable
    """

    # Valid metadata arguments that can be passed to ParameterAccess __init__ method.
    VALID_METADATA_ARGS = (
        "min", "max", "allowed_values", "name", "description", "units", "display_precision"
    )
    # Automatically-populated metadata fields based on inferred type of the parameter and
    # writeable status depending on specified accessors
    AUTO_METADATA_FIELDS = ("type", "writeable")

    def __init__(self, path, getter=None, setter=None, **kwargs):
        """Initialise the BaseParameterAccessor instance.

        This constructor initialises the BaseParameterAccessor instance, storing
        the path of the parameter, its set/get accessors and setting metadata fields based
        on the the specified keyword arguments

        :param path: path of the parameter within the tree
        :param getter: get method for the parameter, or a value if read-only constant
        :param setter: set method for the parameter
        :param kwargs: keyword argument list for metadata fields to be set; these must be from
                       the allow list specified in ParameterAccessor.allowed_metadata
        """
        # Initialise path, getter and setter
        self.path = path[:-1]
        self._get = getter
        self._set = setter

        # Initialize metadata dict
        self.metadata = {}

        # Check metadata keyword arguments are valid
        for arg in kwargs:
            if arg not in BaseParameterAccessor.VALID_METADATA_ARGS:
                raise ParameterTreeError("Invalid metadata argument: {}".format(arg))

        # Update metadata keywords from arguments
        self.metadata.update(kwargs)

        # Set the writeable metadata field based on specified accessors
        if not callable(self._set) and callable(self._get):
            self.metadata["writeable"] = False
        else:
            self.metadata["writeable"] = True

    def get(self, with_metadata=False):
        """Get the value of the parameter.

        This method returns the value of the parameter, or the value returned
        by the get accessor if one is defined (i.e. is callable). If the with_metadata argument
        is true, the value is returned in a dictionary including all metadata for the
        parameter.

        :param with_metadata: include metadata in the response when set to True
        :returns value of the parameter
        """
        # Determine the value of the parameter by calling the getter or simply from the stored
        # value
        if callable(self._get):
            value = self._get()
        else:
            value = self._get

        # If metadata is requested, replace the value with a dict containing the value itself
        # plus metadata fields
        if with_metadata:
            value = {"value": value}
            value.update(self.metadata)

        return value

    def set(self, value):
        """Set the value of the parameter.

        This method sets the value of the parameter by calling the set accessor
        if defined and callable, otherwise raising an exception.

        :param value: value to set
        """
        # Raise an error if this parameter is not writeable
        if not self.metadata["writeable"]:
            raise ParameterTreeError("Parameter {} is read-only".format(self.path))

        # Raise an error of the value to be set is not of the same type as the parameter. If
        # the metadata type field is set to None, allow any type to be set, or if the value
        # is integer and the parameter is float, also allow as JSON does not differentiate
        # numerics in all cases
        if self.metadata["type"] != "NoneType" and not isinstance(value, self._type):
            if not (isinstance(value, int) and self.metadata["type"] == "float"):
                raise ParameterTreeError(
                    "Type mismatch setting {}: got {} expected {}".format(
                        self.path, type(value).__name__, self.metadata["type"]
                    )
                )

        # Raise an error if allowed_values has been set for this parameter and the value to
        # set is not one of them
        if "allowed_values" in self.metadata and value not in self.metadata["allowed_values"]:
            raise ParameterTreeError(
                "{} is not an allowed value for {}".format(value, self.path)
            )

        # Raise an error if the parameter has a mininum value specified in metadata and the
        # value to set is below this
        if "min" in self.metadata and value < self.metadata["min"]:
            raise ParameterTreeError(
                "{} is below the minimum value {} for {}".format(
                    value, self.metadata["min"], self.path
                )
            )

        # Raise an error if the parameter has a maximum value specified in metadata and the
        # value to set is above this
        if "max" in self.metadata and value > self.metadata["max"]:
            raise ParameterTreeError(
                "{} is above the maximum value {} for {}".format(
                    value, self.metadata["max"], self.path
                )
            )

        # Set the new parameter value, either by calling the setter or updating the local
        # value as appropriate
        response = None
        if callable(self._set):
            response = self._set(value)
        elif not callable(self._get):
            self._get = value

        return response


class BaseParameterTree(object):
    """Base class implementing a tree of parameters and their accessors.

    This base class implements an arbitrarily-structured, recursively-managed tree of parameters and
    the appropriate accessor methods that are used to read and write those parameters. Its
    particular use is in the definition of a tree of parameters for an API adapter and help
    interfacing of those to the underlying device or object.
    """

    METADATA_FIELDS = ["name", "description"]

    def __init__(self, tree, mutable=False):
        """Initialise the BaseParameterTree object.

        This constructor recursively initialises the BaseParameterTree object, based on the
        parameter tree dictionary passed as an argument. This is done recursively, so that a
        parameter tree can have arbitrary depth and contain other BaseParameterTree instances
        as necessary.

        Initialisation syntax for BaseParameterTree is made by passing a dict representing the tree
        as an argument. Children of a node at any level of the tree are described with
        dictionaries/lists e.g.

          {"parent" : {"childA" : {...}, "childB" : {...}}}
          {"parent" : [{...}, {...}]}

        Leaf nodes can be one of the following formats:

          value   -  (value,)  -  (value, {metadata})
          getter  -  (getter,) -  (getter, {metadata})
          (getter, setter)     -  (getter, setter, {metadata})

        The following tags will also be treated as metadata:

          name - A printable name for that branch of the tree
          description - A printable description for that branch of the tree

        :param tree: dict representing the parameter tree
        :param mutable: Flag, setting the tree
        """
        # Flag, if set to true, allows nodes to be replaced and new nodes created
        self.mutable = mutable

        # list of paths to mutable parts. Not sure this is best solution
        self.mutable_paths = []

        # Recursively check and initialise the tree
        self._tree = self._build_tree(tree)

    @property
    def tree(self):
        """Return tree object for this parameter tree node.

        Used internally for recursive descent of parameter trees.
        """
        return self._tree

    def get(self, path, with_metadata=False):
        """Get the values of parameters in a tree.

        This method returns the values at and below a specified path in the parameter tree.
        This is done by recursively populating the tree with the current values of parameters,
        returning the result as a dictionary.

        :param path: path in tree to get parameter values for
        :param with_metadata: include metadata in the response when set to True
        :returns: dict of parameter tree at the specified path
        """
        # Split the path by levels, truncating the last level if path ends in trailing slash
        levels = path.split('/')
        if levels[-1] == '':
            del levels[-1]

        # Initialise the subtree before descent
        subtree = self._tree

        # If this is single level path, return the populated tree at the top level
        if not levels:
            return self._populate_tree(subtree, with_metadata)

        # Descend the specified levels in the path, checking for a valid subtree of the appropriate
        # type
        for level in levels:
            if level in self.METADATA_FIELDS and not with_metadata:
                raise ParameterTreeError("Invalid path: {}".format(path))
            try:
                if isinstance(subtree, dict):
                    subtree = subtree[level]
                elif isinstance(subtree, self.accessor_cls):
                    subtree = subtree.get(with_metadata)[level]
                else:
                    subtree = subtree[int(level)]
            except (KeyError, ValueError, IndexError):
                raise ParameterTreeError("Invalid path: {}".format(path))

        # Return the populated tree at the appropriate path
        return self._populate_tree({levels[-1]: subtree}, with_metadata)

    def set(self, path, data, replace=False):
        """Set the values of the parameters in a tree.

        This method sets the values of parameters in a tree, based on the data passed to it
        as a nested dictionary of parameter and value pairs. The updated parameters are merged
        into the existing tree recursively.

        :param path: path to set parameters for in the tree
        :param data: nested dictionary representing values to update at the path
        :param replace: if set to true then the structure is replaced rather than merged
        """
        # Expand out any lists/tuples
        data = self._build_tree(data)

        # Get subtree from the node the path points to
        levels = path.split('/')
        if levels[-1] == '':
            del levels[-1]

        merge_parent = None
        merge_child = self._tree

        # Descend the tree and validate each element of the path
        for level in levels:
            if level in self.METADATA_FIELDS:
                raise ParameterTreeError("Invalid path: {}".format(path))
            try:
                merge_parent = merge_child
                if isinstance(merge_child, dict):
                    merge_child = merge_child[level]
                else:
                    merge_child = merge_child[int(level)]
            except (KeyError, ValueError, IndexError):
                raise ParameterTreeError("Invalid path: {}".format(path))

        # Add trailing / to paths where necessary
        if path and path[-1] != '/':
            path += '/'

        # Merge data with tree
        if replace:
            if not self.mutable:
                raise ParameterTreeError("Invalid Replace Attempt: Tree Not Mutable")
            merged = data
        else:
            merged = self._merge_tree(merge_child, data, path)

        # Add merged part to tree, either at the top of the tree or at the
        # appropriate level speicfied by the path
        if not levels:
            self._tree = merged
            return
        if isinstance(merge_parent, dict):
            merge_parent[levels[-1]] = merged
        else:
            merge_parent[int(levels[-1])] = merged

    def replace(self, path, data):
        """Replaces a branch of parameters in a tree.

        This method sets the values of parameters in a tree, based on the data passed to it
        as a nested dictionary of parameter and value pairs. Any structure below the insertion
        point in the exising tree is replaced with this new structure.

        :param path: path to set parameters for in the tree
        :param data: nested dictionary representing structure to replace at the path
        """
        self.set(path, data, replace=True)

    def delete(self, path=''):
        """
        Remove Parameters from a Mutable Tree.

        This method deletes selected parameters from a tree, if that tree has been flagged as
        Mutable. Deletion of Branch Nodes means all child nodes of that Branch Node are also deleted

        :param path: Path to selected Parameter Node in the tree
        """
        if not self.mutable and not any(path.startswith(part) for part in self.mutable_paths):
            raise ParameterTreeError("Invalid Delete Attempt: Tree Not Mutable")

        # Split the path by levels, truncating the last level if path ends in trailing slash
        levels = path.split('/')
        if levels[-1] == '':
            del levels[-1]

        subtree = self._tree

        if not levels:
            subtree.clear()
            return
        try:
            # Traverse down the path, based on hwo path navigation works in the Set Method above
            for level in levels[:-1]:

                # If the subtree is a dict, the subtree is a normal branch, continue traversal. If
                # it is not a dict the subtree is a list so the next path is indexed by the level
                if isinstance(subtree, dict):
                    subtree = subtree[level]
                else:
                    subtree = subtree[int(level)]

            # Once at the second to last part of the path, delete whatever comes next
            if isinstance(subtree, list):
                subtree.pop(int(levels[-1]))
            else:
                subtree.pop(levels[-1])
        except (KeyError, ValueError, IndexError):
            raise ParameterTreeError("Invalid path: {}".format(path))

    def _build_tree(self, node, path=''):
        """Recursively build and expand out a tree or node.

        This internal method is used to recursively build and expand a tree or node,
        replacing elements as found with appropriate types, e.g. ParameterAccessor for
        a set/get pair, the internal tree of a nested ParameterTree.

        :param node: node to recursively build
        :param path: path to node within overall tree
        :returns: built node
        """
        # If the node is a parameter tree instance, replace with its own built tree
        if isinstance(node, type(self)):
            if node.mutable:
                self.mutable_paths.append(path)
            return node.tree  # this breaks the mutability of the sub-tree. hmm

        # Convert node tuple into the corresponding ParameterAccessor, depending on type of
        # fields
        if isinstance(node, tuple):
            if len(node) == 1:
                # Node is (value)
                param = self.accessor_cls(path, node[0])

            elif len(node) == 2:
                if isinstance(node[1], dict):
                    # Node is (value, {metadata})
                    param = self.accessor_cls(path, node[0], **node[1])
                else:
                    # Node is (getter, setter)
                    param = self.accessor_cls(path, node[0], node[1])

            elif len(node) == 3 and isinstance(node[2], dict):
                # Node is (getter, setter, {metadata})
                param = self.accessor_cls(path, node[0], node[1], **node[2])

            else:
                raise ParameterTreeError("{} is not a valid leaf node".format(repr(node)))

            return param

        # Convert list or non-callable tuple to enumerated dict
        if isinstance(node, list):
            return [self._build_tree(elem, path=path) for elem in node]

        # Recursively check child elements
        if isinstance(node, dict):
            return {k: self._build_tree(
                v, path=path + str(k) + '/') for k, v in node.items()}

        return node

    def __remove_metadata(self, node):
        """Remove metadata fields from a node.

        Used internally to return a parameter tree without metadata fields

        :param node: tree node to return without metadata fields
        :returns: generator yeilding items in node minus metadata
        """
        for key, val in node.items():
            if key not in self.METADATA_FIELDS:
                yield key, val

    def _populate_tree(self, node, with_metadata=False):
        """Recursively populate a tree with values.

        This internal method recursively populates the tree with parameter values, or
        the results of the accessor getters for nodes. It is called by the get() method to
        return the values of parameters in the tree.

        :param node: tree node to populate and return
        :param with_metadata: include parameter metadata with the tree
        :returns: populated node as a dict
        """
        # If this is a branch node recurse down the tree
        if isinstance(node, dict):
            if with_metadata:
                branch = {
                    k: self._populate_tree(v, with_metadata) for k, v
                    in node.items()
                }
            else:
                branch = {
                    k: self._populate_tree(v, with_metadata) for k, v
                    in self.__remove_metadata(node)
                }
            return branch

        if isinstance(node, list):
            return [self._populate_tree(item, with_metadata) for item in node]

        # If this is a leaf node, check if the leaf is a r/w tuple and substitute the
        # read element of that tuple into the node
        if isinstance(node, self.accessor_cls):
            return node.get(with_metadata)

        return node

    def _merge_tree(self, node, new_data, cur_path):
        """Recursively merge a tree with new values.

        This internal method recursively merges a tree with new values. Called by the set()
        method, this allows parameters to be updated in place with the specified values,
        calling the parameter setter in specified in an accessor. The type of any updated
        parameters is checked against the existing parameter type.

        :param node: tree node to populate and return
        :param new_data: dict of new data to be merged in at this path in the tree
        :param cur_path: current path in the tree
        :returns: the update node at this point in the tree
        """
        # Recurse down tree if this is a branch node
        if isinstance(node, dict) and isinstance(new_data, dict):
            try:
                update = {}
                for k, v in self.__remove_metadata(new_data):
                    mutable = self.mutable or any(
                        cur_path.startswith(part) for part in self.mutable_paths
                    )
                    if mutable and k not in node:
                        node[k] = {}
                    update[k] = self._merge_tree(node[k], v, cur_path + k + '/')
                    node.update(update)
                return node
            except KeyError as key_error:
                raise ParameterTreeError(
                    'Invalid path: {}{}'.format(cur_path, str(key_error)[1:-1])
                )
        if isinstance(node, list) and isinstance(new_data, (dict, list)):
            try:
                for i, val in enumerate(new_data):
                    node[i] = self._merge_tree(node[i], val, cur_path + str(i) + '/')
                return node
            except IndexError as index_error:
                raise ParameterTreeError(
                    'Invalid path: {}{} {}'.format(cur_path, str(i), str(index_error))
                )

        # Update the value of the current parameter, calling the set accessor if specified and
        # validating the type if necessary.
        if isinstance(node, self.accessor_cls):
            self._set_node(node, new_data)
        else:
            # Validate type of new node matches existing
            if not self.mutable and type(node) is not type(new_data):
                if not any(cur_path.startswith(part) for part in self.mutable_paths):
                    raise ParameterTreeError('Type mismatch updating {}: got {} expected {}'.format(
                        cur_path[:-1], type(new_data).__name__, type(node).__name__
                    ))
            node = new_data

        return node

    def _set_node(self, node, data):
        """Set the value of a node to the specified data.

        This method trivially sets a specified node to the data supplied. It is exposed as a method
        to allow derived classes to override it and add behaviour as necessary.

        :param node: tree node to set value of
        :param data: data to node value to
        """
        node.set(data)
