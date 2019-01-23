"""ParameterTree - classes representing a tree of parameters and their accessor methods.

This module implements an arbitrarily-structured, recursively-managed tree of parameters and
the appropriate accessor methods that are used to read and write those parameters. Its
particular use is in the definition of a tree of parameters for an API adapter and help
interfacing of those to the underlying device or object.

James Hogge, Tim Nicholls, STFC Application Engineering Group.
"""
import warnings


class ParameterTreeError(Exception):
    """Simple error class for raising parameter tree parameter tree exceptions."""

    pass


class ParameterAccessor(object):
    """Container class representing accessor methods for a parameter.

    This class implements a parameter accessor, provding set and get methods
    for parameters requiring calls to access them, or simply returning the
    appropriate value if the parameter is a read-only constant.
    """

    def __init__(self, path, getter=None, setter=None):
        """Initialise the ParameterAccessor instance.

        This constructor initialises the ParameterAccessor instance, storing
        the path of the parameter and its set/get accessors.

        :param path: path of the parameter within the tree
        :param getter: get method for the parameter, or a value if read-only constant
        :param setting: set method for the parameter
        """
        self.path = path[:-1]
        self._get = getter
        self._set = setter

    def get(self):
        """Get the value of the parameter.

        This method returns the value of the parameter, or the value returned
        by the get accessor if one is defined (i.e. is callable).

        :returns value of the parameter
        """
        if callable(self._get):
            return self._get()
        else:
            return self._get

    def set(self, value):
        """Set the value of the parameter.

        This method sets the value of the parameter by calling the set accessor
        if defined and callable, otherwise raising an exception.

        :param value: value to set
        """
        if callable(self._set):
            return self._set(value)
        elif not callable(self._get):
            self._get = value
        else:
            raise ParameterTreeError("Parameter {} is read-only".format(self.path))


class ParameterTree(object):
    """Class implementing a tree of parameters and their accessors.

    This class implements an arbitrarily-structured, recursively-managed tree of parameters and
    the appropriate accessor methods that are used to read and write those parameters. Its
    particular use is in the definition of a tree of parameters for an API adapter and help
    interfacing of those to the underlying device or object.
    """

    def __init__(self, tree):
        """Initialise the ParameterTree object.

        This constructor recursively initialises the ParameterTree object, based on the parameter
        tree dictionary passed as an argument. This is done recursively, so that a parameter tree
        can have arbitrary depth and contain other ParameterTree instances as necessary.

        :param tree: dict representing the parameter tree
        """
        # Create empty callback list
        self.__callbacks = []

        # Recursively check and initialise the tree
        self.__tree = self.__recursive_build_tree(tree)

    def get(self, path):
        """Get the values of parameters in a tree.

        This method returns the values at and below a specified path in the parameter tree.
        This is done by recursively populating the tree with the current values of parameters,
        returning the result as a dictionary.

        :param path: path in tree to get parameter values for
        :returns: dict of parameter tree at the specified path
        """
        # Split the path by levels, truncating the last level if path ends in trailing slash
        levels = path.split('/')
        if levels[-1] == '':
            del levels[-1]

        # Initialise the subtree before descent
        subtree = self.__tree
        # If this is single level path, return the populated tree at the top level
        if len(levels) == 0:
            return self.__recursive_populate_tree(subtree)

        # Descend the specified levels in the path, checking for a valid subtree of the appropriate
        # type
        for l in levels:
            try:
                if isinstance(subtree, dict):
                    subtree = subtree[l]
                elif isinstance(subtree, ParameterAccessor):
                    subtree = subtree.get()[l]
                else:
                    subtree = subtree[int(l)]
            except (KeyError, ValueError, IndexError):
                raise ParameterTreeError("Invalid path: {}".format(path))

        # Return the populated tree at the appropriate path
        return self.__recursive_populate_tree({levels[-1]: subtree})

    def set(self, path, data):
        """Set the values of the parameters in a tree.

        This method sets the values of parameters in a tree, based on the data passed to it
        as a nested dictionary of parameter and value pairs. The updated parameters are merged
        into the existing tree recursively.

        :param path: path to set parameters for in the tree
        :param data: nested dictionary representing values to update at the path
        """
        # Expand out any lists/tuples
        data = self.__recursive_build_tree(data)

        # Get subtree from the node the path points to
        levels = path.split('/')
        if levels[-1] == '':
            del levels[-1]

        merge_parent = None
        merge_child = self.__tree

        # Descend the tree and validate each element of the path
        for l in levels:
            try:
                merge_parent = merge_child
                if isinstance(merge_child, dict):
                    merge_child = merge_child[l]
                else:
                    merge_child = merge_child[int(l)]
            except (KeyError, ValueError, IndexError):
                raise ParameterTreeError("Invalid path: {}".format(path))

        # Add trailing / to paths where necessary
        if len(path) and path[-1] != '/':
            path += '/'

        # Merge data with tree
        merged = self.__recursive_merge_tree(merge_child, data, path)

        # Add merged part to tree, either at the top of the tree or at the
        # appropriate level speicfied by the path
        if len(levels) == 0:
            self.__tree = merged
            return
        if isinstance(merge_parent, dict):
            merge_parent[levels[-1]] = merged
        else:
            merge_parent[int(levels[-1])] = merged

    def add_callback(self, path, callback):
        """Add a callback to a given path in the tree - DEPRECATED.

        This now deprecated method adds a callback to the specified path in the
        tree. Originally intended to allow set() calls to update values in the
        underlying object or device represented by the tree, this has been
        replaced by the symmetric read/write ParameterAccessor mechanism. Its
        remaining function could be to allow side-effects during set() calls.

        :param path: path to add callback for
        :param callback: method to be called when the appropriate set() call is made
        """
        warnings.warn(
            "Callbacks in parameter trees are deprecated, use parameter accessors instead",
            DeprecationWarning
        )
        self.__callbacks.append([path, callback])

    def __recursive_build_tree(self, node, path=''):
        """Recursively build and expand out a tree or node.

        This internal method is used to recursively build and expand a tree or node,
        replacing elements as found with appropriate types, e.g. ParameterAccessor for
        a set/get pair, the internal tree of a nested ParameterTree.

        :param node: node to recursively build
        :param path: path to node within overall tree
        :returns: built node
        """

        # If the node is a ParameterTree instance, replace with its own built tree
        if isinstance(node, ParameterTree):
            # Merge in callbacks in node if present
            for c in node.__callbacks:
                self.add_callback(path + c[0], c[1])
            return node.__tree

        # Convert 2-tuple of one or more callables into a read-write accessor pair
        if isinstance(node, tuple) and len(node) == 2:
            return ParameterAccessor(path, node[0], node[1])

        # Convert list or non-callable tuple to enumerated dict
        if isinstance(node, list):
            return [self.__recursive_build_tree(elem, path=path) for elem in node]

        # Recursively check child elements
        if isinstance(node, dict):
            return {k: self.__recursive_build_tree(
                v, path=path + str(k) + '/') for k, v in node.items()}

        return node

    def __recursive_populate_tree(self, node):
        """Recursively populate a tree with values.

        This internal method recursively populates the tree with parameter values, or
        the results of the accessor getters for nodes. It is called by the get() method to
        return the values of parameters in the tree.

        :param node: tree node to populate and return
        :returns: populated node as a dict
        """
        # If this is a branch node recurse down the tree
        if isinstance(node, dict):
            return {k: self.__recursive_populate_tree(v) for k, v in node.items()}

        if isinstance(node, list):
            return [self.__recursive_populate_tree(item) for item in node]

        # If this is a leaf node, check if the leaf is a r/w tuple and substitute the
        # read element of that tuple into the node
        if isinstance(node, ParameterAccessor):
            return node.get()

        return node

    # Replaces values in data_tree with values from new_data
    def __recursive_merge_tree(self, node, new_data, cur_path):
        """Recursively merge a tree with new values.

        This internal method recursively merges a tree with new values. Called by the set()
        method, this allows parameters to be updated in place with the specified values,
        calling the parameter setter in specified in an accessor. The type of any updated
        parameters is checked against the existing parameter type. Any callbacks registed
        at the current path at called.

        :param node: tree node to populate and return
        :param new_data: dict of new data to be merged in at this path in the tree
        :param cur_path: current oath in the tree
        :returns: the update node at this point in the tree
        """
        # Recurse down tree if this is a branch node
        if isinstance(node, dict) and isinstance(new_data, dict):
            try:
                node.update({k: self.__recursive_merge_tree(
                    node[k], v, cur_path + k + '/') for k, v in new_data.items()})
                return node
            except KeyError as e:
                raise ParameterTreeError('Invalid path: {}{}'.format(cur_path, str(e)[1:-1]))
        if isinstance(node, list) and isinstance(new_data, dict):
            try:
                for i, v in enumerate(new_data):
                    node[i] = self.__recursive_merge_tree(node[i], v, cur_path + str(i) + '/')
                return node
            except IndexError as e:
                raise ParameterTreeError('Invalid path: {}{} {}'.format(cur_path, str(i), str(e)))

        # Update the value of the current parameter, calling the set accessor if specified and
        # validating the type if necessary.
        if isinstance(node, ParameterAccessor):
            node.set(new_data)
        else:
            # Validate type of new node matches existing
            if type(node) is not type(new_data):
                raise ParameterTreeError('Type mismatch updating {}: got {} expected {}'.format(
                    cur_path[:-1], type(new_data).__name__, type(node).__name__
                ))
            node = new_data

        # Call any callbacks specified at this path
        for c in self.__callbacks:
            if cur_path.startswith(c[0]):
                c[1](cur_path, new_data)

        return node
