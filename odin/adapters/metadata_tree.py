from parameter_tree import ParameterTree, ParameterAccessor

class MetadataParameterError(Exception):
    pass

class MetadataParameterAccessor(ParameterAccessor):
    """Container class representing a leaf node on the tree.
    
    This class implements a parameter accessor, provding set and get methods
    for parameters requiring calls to access them, or simply returning the
    appropriate value if the parameter is a read-only constant. It also supports
    the addition of metadata to control access to the parameter.

    Available parameters:
    min (?), , Parameter must satisfy parameter >= min when set
    max (?), , Parameter must satisfy parameter <= max when set
    type (string), default: Type of parameter when set, Specifies a type for the parameter & can be set to None to allow any type
    writeable (boolean), default: True (False if write is impossible), Used to disable write access to a parameter
    available (list[?]), , Gives a list of specific values the parameter must hold
    units (string), , Extra information to be passed to the client if requested
    name, , A printable, human readable name for the parameter to be displayed on a webpage
    dp, 2, Number of decimal places to display to (set 0 to ignore)
    """

    def __init__(self, path, getter=None, setter=None, **kwargs):
        """Initialises the accessor class and checks metadata.
        "type" and "writeable" determined automatically unless otherwise specified.
        """

        ParameterAccessor.__init__(self, path, getter, setter)

        self.metadata = {}

        #Check rw capability of variable
        self.metadata["writeable"] = True
        self.metadata["type"] = type(self.get()).__name__
        
        if self.metadata["type"] in ["int", "float"]:
            self.metadata["dp"] = 2

        #Not a value type and no setter => Default to not writeable
        if not callable(self._set) and callable(self._get):
            self.metadata["writeable"] = False

        #Check arguments are valid
        valid_args = ["min", "max", "type", "writeable", "available", "units", "name", "dp", "description"]
        for kw in kwargs:
            if not kw in valid_args:
                raise MetadataParameterError("Invalid argument: {}".format(kw))

        #Take other values from keyword arguments
        self.metadata.update(kwargs)

    def set(self, value):
        """Sets the parameter with a given value if possible.

        :param value: The value to assign the parameter
        """        

        if not self.metadata["writeable"]:
            raise MetadataParameterError("Parameter {} is read-only".format(self.path))

        if not self.metadata["type"] == None and not type(value).__name__ == self.metadata["type"]:
            #This conversion is allowed since JSON does not distinguish numerics
            if not (type(value) == int and self.metadata["type"] == "float"):
                raise MetadataParameterError("Type mismatch updating {}: got {} expected {}".format(
                    self.path, type(value).__name__, self.metadata["type"]))

        if "available" in self.metadata and not value in self.metadata["available"]:
            raise MetadataParameterError("{} is not an allowed value for {}".format(value, self.path))

        if "min" in self.metadata and value < self.metadata["min"]:
            raise MetadataParameterError("{} is below the minimum value {} for {}".format(value, self.metadata["min"], self.path))

        if "max" in self.metadata and value > self.metadata["max"]:
            raise MetadataParameterError("{} is above the maximum value {} for {}".format(value, self.metadata["max"], self.path))

        ParameterAccessor.set(self, value)

    def get(self, metadata=False):
        """Gets the current value of the parameter.

        :param metadata: flag to include the metadata with the value
        :returns: The value of the parameter
        """

        value = ParameterAccessor.get(self)
        
        if metadata:
            value = {"value" : value}
            value.update(self.metadata)

        return value
        
                    

class MetadataTree(ParameterTree):
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
        
        Construction syntax:
        Children of a node are described with dictionaries/lists e.g.
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
        """
        # Create empty callback list
        self.__callbacks = []

        self.metadata_tags = ["name", "description", "list"]

        # Recursively check and initialise the tree
        self.__tree = self.__recursive_build_tree(tree)

    def get(self, path, metadata=False):
        """Get the values of parameters in a tree.

        This method returns the values at and below a specified path in the parameter tree.
        This is done by recursively populating the tree with the current values of parameters,
        returning the result as a dictionary.

        :param path: path in tree to get parameter values for
        :param metadata: flag to include metadata in the tree
        :returns: dict of parameter tree at the specified path
        """
        # Split the path by levels
        levels = path.split('/')

        # Initialise the subtree before descent
        subtree = self.__tree

        # If this is single level path, return the populated tree at the top level
        if levels == ['']:
            return self.__recursive_populate_tree(subtree, metadata=metadata)

        # Descend the specified levels in the path, checking for a valid subtree
        for l in levels:
            # Check if next level of path is valid
            try:
                if l in self.metadata_tags and not metadata:
                    raise MetadataParameterError("Invalid path: {}".format(path))

                if isinstance(subtree, dict):
                    subtree = subtree[l]
                else:
                    subtree = subtree[int(l)]
            except (KeyError, ValueError, IndexError):
                raise MetadataParameterError("Invalid path: {}".format(path))

        # Return the populated tree at the appropriate path
        return self.__recursive_populate_tree({levels[-1]: subtree}, metadata=metadata)

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
        if levels == ['']:
            levels = []

        merge_parent = None
        merge_child = self.__tree
    
        # Descend the tree and validate each element of the path
        for l in levels:
            # Check if next level of path is valid
            try:
                if l in self.metadata_tags:
                    raise MetadataParameterError("Invalid path: {}".format(path))

                merge_parent = merge_child
                if isinstance(merge_child, dict):
                    merge_child = merge_child[l]
                else:
                    merge_child = merge_child[int(l)]
            except (KeyError, ValueError, IndexError):
                raise MetadataParameterError("Invalid path: {}".format(path))
 
        # Add trailing / to paths where necessary
        if len(path) and path[-1] != '/':
            path += '/'

        # Merge data with tree
        merged = self.__recursive_merge_tree(merge_child, data, path)

        # Add merged part to tree, either at the top of the tree or at the
        # appropriate level speicfied by the path
        if levels == []:
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

        # Convert tuples to their corresponding Accessor
        if isinstance(node, tuple):
            if len(node) == 1:
                # (value)
                return MetadataParameterAccessor(path, node[0])
            elif len(node) == 2:
                if isinstance(node[1], dict):
                    # (value, {metadata})
                    return MetadataParameterAccessor(path, node[0], **node[1])
                else:
                    # (getter, setter)
                    return MetadataParameterAccessor(path, node[0], node[1])
            elif len(node) == 3 and isinstance(node[2], dict):
                # (getter, setter, {metadata})
                return MetadataParameterAccessor(path, node[0], node[1], **node[2])
            else:
                raise MetadataParameterError("{} is not a valid leaf node".format(repr(node)))

        # Recurse through list/dict
        if isinstance(node, list):
            return [self.__recursive_build_tree(elem, path=path) for elem in node]
        if isinstance(node, dict):
            return {k: self.__recursive_build_tree(
                v, path=path + k + '/') for k, v in node.items()}

        # Use accessors directly
        if isinstance(node, MetadataParameterAccessor):
            return node

        if len(path) > 1 and path.split('/')[-2] in self.metadata_tags:
            return node

        return MetadataParameterAccessor(path, node)

    def __remove_metadata(self, node):
        for k, v in node.items():
            if not k in self.metadata_tags:
                yield k, v

    def __recursive_populate_tree(self, node, metadata=False):
        """Recursively populate a tree with values.

        This internal method recursively populates the tree with parameter values, or
        the results of the accessor getters for nodes. It is called by the get() method to
        return the values of parameters in the tree.

        :param node: tree node to populate and return
        :param metadata: flag to include metadata within the tree
        :returns: populated node as a dict
        """
        # If this is a branch node recurse down the tree
        if isinstance(node, dict):
            if metadata:
                return {k: self.__recursive_populate_tree(v, metadata=metadata) for k, v in node.items()}
            else:
                return {k: self.__recursive_populate_tree(v, metadata=metadata) for k, v in self.__remove_metadata(node)}

        if isinstance(node, list):
            return [self.__recursive_populate_tree(item, metadata=metadata) for item in node]

        # If this is a leaf node, check if the leaf is a r/w tuple and substitute the
        # read element of that tuple into the node
        if isinstance(node, MetadataParameterAccessor):
            return node.get(metadata=metadata)

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
        if isinstance(node, dict):
            try:
                node.update({k: self.__recursive_merge_tree(
                    node[k], v, cur_path + k + '/') for k, v in self.__remove_metadata(new_data)})
                return node
            except KeyError as e:
                raise MetadataParameterError('Invalid path: {}{}'.format(cur_path, str(e)[1:-1]))
        if isinstance(node, list):
            try:
                for i, v in enumerate(new_data):
                    node[i] = self.__recursive_merge_tree(node[i], v, cur_path + str(i) + '/')
                return node
            except IndexError as e:
                raise MetadataParameterError('Invalid path: {}{}'.format(cur_path, str(e)[1:-1]))

        # Update the value of the current parameter, calling the set accessor if specified and
        # validating the type if necessary.
        if isinstance(node, MetadataParameterAccessor) and isinstance(new_data, MetadataParameterAccessor):
            node.set(new_data.get())
        else:
            raise MetadataParameterError("Merging error: the data passed to set() is incompatible with {}".format(cur_path))

        # Call any callbacks specified at this path
        for c in self.__callbacks:
            if cur_path.startswith(c[0]):
                c[1](cur_path, new_data)

        return node

