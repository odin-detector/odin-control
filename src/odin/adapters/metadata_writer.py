import logging
from concurrent import futures
from odin.adapters.adapter import (ApiAdapter, ApiAdapterRequest, ApiAdapterResponse,
                                   request_types, response_types)
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from odin.util import decode_request_body
from os import path

import h5py


CONFIG_FILE_NAME = "file_name"
DEFAULT_FILE_NAME = "test_0001.h5"


class MetadataWriterAdapter(ApiAdapter):
    """Metadata Writer Adapter Class for the Odin Server

    """

    def __init__(self, **kwargs):
        """Init the Adapter"""

        super(MetadataWriterAdapter, self).__init__(**kwargs)

        file_name = self.options.get(CONFIG_FILE_NAME, DEFAULT_FILE_NAME)
        metadata = {'test': {"test_1": "One"}}
        self.metadata_writer = MetadataWriter(file_name, metadata)


    @response_types("application/json", default="application/json")
    def get(self, path, request, with_metadata=False):
        """
        Handle a HTTP GET request from a client, passing this to the Live Viewer object.

        :param path: The path to the resource requested by the GET request
        :param request: Additional request parameters
        :return: The requested resource, or an error message and code if the request was invalid.
        """
        response = self.metadata_writer.get(path, with_metadata)
        status_code = self.metadata_writer.status_code
        return ApiAdapterResponse(response, content_type='application/json', status_code=status_code)

    @request_types("application/json", "application/vnd.odin-native")
    @response_types("application/json", default="application/json")
    def put(self, path, request):
        """
        Handle a HTTP PUT i.e. set request.

        :param path: the URI path to the resource
        :param data: the data to PUT to the resource
        """
        data = decode_request_body(request)
        self.metadata_writer.set(path, data)
        response = self.metadata_writer.get(path)
        status_code = self.metadata_writer.status_code
        return ApiAdapterResponse(response, content_type='application/json', status_code=status_code)


class MetadataWriter(object):

    def __init__(self, file_name, metadata_init):

        self.file_name = file_name
        self.metadata = ParameterTree(metadata_init)
        self.dir = ""

        self.populate_param_tree()

        self.status_code = 200
        self.status_message = ""

    def populate_param_tree(self):
        self.param_tree = ParameterTree({
            "name": "Metadata Writer",
            "file": (lambda: self.file_name, self.set_file),
            "file_dir": (lambda: self.dir, self.set_file_dir),
            "metadata": self.metadata,
            "write": (None, self.write_metadata)
        })

    # @property
    # def status_code(self):
    #     """
    #     Resets potential error code when accessed to avoid duplicate error codes being returned
    #     """
    #     code = self._status_code
    #     self.status_code = 200
    #     return code

    def get(self, path, with_metadata=False):
        """
        Handle a HTTP get request.

        Checks if the request is for the image or another resource, and responds accordingly.
        :param path: the URI path to the resource requested
        :param request: Additional request parameters.
        :return: the requested resource,or an error message and code, if the request is invalid.
        """

        return self.param_tree.get(path, with_metadata)

    def set(self, path, data):

        # logging.debug("PATH: %s", path)
        if path.startswith("metadata"):
            logging.debug("Writing to metadata tree")
            try:
                self.param_tree.set(path, data)
            except ParameterTreeError:
                logging.debug("Param Tree Error. Need to add to metadata tree")
                path = path.split('/')[1:]
                logging.debug(path)
                for part_path in path:
                    # extend data dict to have full path, for recurisve merge
                    data = {part_path: data}
                logging.debug(data)
                met_dict = self.metadata.get('')
                logging.debug("Metadata Dict: %s", met_dict)
                new_met_dict = self.recursive_merge_dicts(met_dict, data)

                logging.debug("New Tree: %s", new_met_dict)
                self.metadata = ParameterTree(new_met_dict)
                logging.debug("New Metadata ParamTree: %s", self.metadata.get(""))
                self.populate_param_tree()
                
        else:
            self.param_tree.set(path, data)

    def set_file(self, file_name):
        """
        Set the name of the file. Does not check if the file exists yet, as this could be set before
        the file is created.
        """
        if file_name.endswith((".h5", ".hdf5")):
            self.file_name = file_name

    def set_file_dir(self, dir):
        """
        Set the location of the file. Does not check if the directory exists yet, as this can be set
        before the directory is created if need be.
        """
        self.dir = dir

    # def set_metadata(self, metadata):
    #     """
    #     Modifies the metadata dictionary by merging the provided dictionary into it. Can handle
    #     nested dictionaries if required.
    #     """

    #     if not isinstance(metadata, dict):
    #         self.status_code = 400
    #         self.status_message = "Expected dict, got {}".format(metadata)
    #         return

    #     for key in metadata:
    #         node = self.metadata.get(key, None)
    #         new_data = metadata[key]
    #         # self.metadata[key] = self.recursive_merge_dicts(node, new_data, key)

    def recursive_merge_dicts(self, node, new_data):
        """
        Merges the two provided dictionaries together, recursivly if a value is also a dict
        """
        logging.debug("RECURSIVE MERGE START")
        logging.debug("Original Dict: %s", node)
        logging.debug("New Dict: %s", new_data)
        if isinstance(node, dict) and isinstance(new_data, dict):
            for key in new_data:
                new_node = node.get(key, None)
                data = new_data[key]
                if new_node is not None:
                    node[key] = self.recursive_merge_dicts(new_node, data)
                else:
                    node[key] = data
        else:
            node = new_data

        return node

    def write_metadata(self, data):
        """
        Writes the metadata to the h5 file. Will set the status code to an error if opening the file
        fails
        """
        try:
            file_path = path.join(self.dir, self.file_name)
            logging.debug("Opening file at location %s", file_path)
            hdf_file = h5py.File(file_path, 'r+')

        except IOError as err:

            logging.error("Failed to open file: %s", err)
            self.status_code = 400
            self.status_message = "Failed to open h5 file"
            return
        try:
            metadata_group = hdf_file.create_group("metadata")
        except ValueError:
            metadata_group = hdf_file["metadata"]
        self.add_metadata_to_group(self.metadata, metadata_group)

        hdf_file.close()

    def add_metadata_to_group(self, metadata, group):

        for key in metadata:
            if isinstance(metadata[key], dict):
                logging.debug("Creating Metadata Subgroup: %s", key)
                try:
                    sub_group = group.create_group(key)
                except ValueError:
                    sub_group = group[key]
                self.add_metadata_to_group(metadata[key], sub_group)
            else:
                logging.debug("Writing metadata to key %s", key)
                group.attrs[key] = metadata[key]
