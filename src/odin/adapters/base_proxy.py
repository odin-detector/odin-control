"""
Base class implementations for the synchronous and asynchronous proxy adapter implemntations.

This module contains classes that provide the common behaviour for the implementations of the
proxy target and adaprers.

Tim Nicholls, Ashley Neaves STFC Detector Systems Software Group.
"""

import logging
import time
from dataclasses import dataclass

import tornado
import tornado.httpclient
from tornado.escape import json_decode, json_encode

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError


@dataclass
class ProxyRequest:
    """
    Proxy request dataclass.

    This dataclass defines a proxy request that can be passed to the target implementation.
    """

    url: str  #:  URL for the proxy request
    method: str  #: HTTP method (e.g. "GET" or "PUT")
    headers: dict  #: HTTP headers to be included with the request
    timeout: float  #: request timeout in seconds
    data: str = None  #: Data to be sent in the request body


@dataclass
class ProxyResponse:
    """
    Proxy response dataclass.

    This dataclass defines a proxy response object that is passed back from the underlying
    target implementation for processing.
    """

    status_code: int  #: HTTP status code for the request
    body: bytes  #: body of the response to the request


@dataclass
class ProxyError:
    """
    Proxy error dataclass.

    This dataclass defines a proxy error object that is passed back from the underlying target
    implementation in the event that there was a problem with the request.
    """

    status_code: int  #: HTTP status code for the request
    error_string: str  #: readable error string describing the error


class BaseProxyTarget(object):
    """
    Proxy target base class.

    This base class provides the core functionality needed for the concrete synchronous and
    asynchronous implementations. It is not intended to be instantiated directly.
    """

    def __init__(self, name, url, request_timeout):
        """
        Initialise the BaseProxyTarget object.

        Sets up the default state of the base target object, builds the appropriate parameter tree
        to be handled by the containing adapter and sets up the HTTP client for making requests
        to the target.

        :param name: name of the proxy target
        :param url: URL of the remote target
        :param request_timeout: request timeout in seconds
        """
        self.name = name
        self.url = url
        self.request_timeout = request_timeout

        # Initialise default state
        self.status_code = 0
        self.error_string = "OK"
        self.last_update = "unknown"
        self.data = {}
        self.metadata = {}
        self.counter = 0

        # Build a parameter tree representation of the proxy target status
        self.status_param_tree = ParameterTree(
            {
                "url": (lambda: self.url, None),
                "status_code": (lambda: self.status_code, None),
                "error": (lambda: self.error_string, None),
                "last_update": (lambda: self.last_update, None),
            }
        )

        # Build a parameter tree representation of the proxy target data
        self.data_param_tree = ParameterTree((lambda: self.data, None))
        self.meta_param_tree = ParameterTree((lambda: self.metadata, None))

        # Set up default request headers
        self.request_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def remote_get(self, path="", get_metadata=False):
        """
        Get data from the remote target.

        This method requests data from the remote target by issuing a GET request to the target
        URL, and then updates the local proxy target data and status information according to the
        response. The request is sent to the target by the implementation-specific _send_request
        method.

        :param path: path to data on remote target
        :param get_metadata: flag indicating if metadata is to be requested
        """
        # Create a GET request to send to the target
        request = ProxyRequest(
            url=self.url + path,
            method="GET",
            headers=self.request_headers.copy(),
            timeout=self.request_timeout,
        )

        # If metadata is requested, modify the Accept header accordingly
        if get_metadata:
            request.headers["Accept"] += ";metadata=True"

        # Send the request to the remote target
        return self._send_request(request, path, get_metadata)

    def remote_set(self, path, data):
        """
        Set data on the remote target.

         his method sends data to the remote target by issuing a PUT request to the target
        URL, and then updates the local proxy target data and status information according to the
        response. The request is sent to the target by the implementation-specific _send_request
        method.

        :param path: path to data on remote target
        :param data: data to set on remote target
        """
        # Encode the request data as JSON if necessary
        if isinstance(data, dict):
            data = json_encode(data)

        # Create a PUT request to send to the target
        request = ProxyRequest(
            url=self.url + path,
            method="PUT",
            headers=self.request_headers.copy(),
            timeout=self.request_timeout,
            data=data,
        )

        # Send the request to the remote target
        return self._send_request(request, path)

    def _process_response(self, response, path, get_metadata):
        """
        Process a response from the remote target.

        This method processes the response of a remote target to a request. The response is used to
        update the local proxy target data metadata and status as appropriate. If the request failed
        the returned exception is decoded and the status updated accordingly.

        :param response: HTTP response from the target, or an exception if the response failed
        :param path: path of data being updated
        :param get_metadata: flag indicating if metadata was requested
        """
        # Update the timestamp of the last request in standard format
        self.last_update = tornado.httputil.format_timestamp(time.time())

        # If an proxy response was received, handle accordingly
        if isinstance(response, ProxyResponse):

            # Decode the reponse body, handling errors by re-processing the repsonse as a proxy
            # error. Otherwise, update the target data and status based on the response.
            try:
                response_body = json_decode(response.body)
            except ValueError as decode_error:
                self._process_response(
                    ProxyError(
                        status_code=415,
                        error_string="Failed to decode response body: {}".format(str(decode_error)),
                    ),
                    path,
                    get_metadata,
                )
            else:

                # Update status code, errror string and data accordingly
                self.status_code = response.status_code
                self.error_string = "OK"

                # Set a reference to the data or metadata to update as necessary
                if get_metadata:
                    data_ref = self.metadata
                else:
                    data_ref = self.data

                # If a path was specified, parse it and descend to the appropriate location in the
                # data struture
                if path:
                    path_elems = path.split("/")

                    # Remove empty string caused by trailing slashes
                    if path_elems[-1] == "":
                        del path_elems[-1]

                    # Traverse down the data tree for each element
                    for elem in path_elems[:-1]:
                        data_ref = data_ref[elem]

                # Update the data or metadata with the body of the response
                for key in response_body:
                    new_elem = response_body[key]
                    data_ref[key] = new_elem

        elif isinstance(response, ProxyError):

            self.status_code = response.status_code
            self.error_string = response.error_string

            logging.error(
                "Proxy target %s request failed (%d): %s ",
                self.name,
                self.status_code,
                self.error_string,
            )


class BaseProxyAdapter(object):
    """
    Proxy adapter base mixin class.

    This mixin class implements the core functionality required by all concrete proxy adapter
    implementations.
    """

    TIMEOUT_CONFIG_NAME = "request_timeout"
    TARGET_CONFIG_NAME = "targets"

    def initialise_proxy(self, proxy_target_cls):
        """
        Initialise the proxy.

        This method initialises the proxy. The adapter options are parsed to determine the list
        of proxy targets and request timeout, then a proxy target of the specified class is created
        for each target. The data, metadata and status structures and parameter trees associated
        with each target are created.

        :param proxy_target_cls: proxy target class appropriate for the specific implementation
        """
        # Set the HTTP request timeout if present in the options
        request_timeout = None
        if self.TIMEOUT_CONFIG_NAME in self.options:
            try:
                request_timeout = float(self.options[self.TIMEOUT_CONFIG_NAME])
                logging.debug("Proxy adapter request timeout set to %f secs", request_timeout)
            except ValueError:
                logging.error(
                    "Illegal timeout specified for proxy adapter: %s",
                    self.options[self.TIMEOUT_CONFIG_NAME],
                )

        # Parse the list of target-URL pairs from the options, instantiating a proxy target of the
        # specified type for each target specified.
        self.targets = []
        if self.TARGET_CONFIG_NAME in self.options:
            for target_str in self.options[self.TARGET_CONFIG_NAME].split(","):
                try:
                    (target, url) = target_str.split("=")
                    self.targets.append(
                        proxy_target_cls(target.strip(), url.strip(), request_timeout)
                    )
                except ValueError:
                    logging.error(
                        "Illegal target specification for proxy adapter: %s", target_str.strip()
                    )

        # Issue an error message if no targets were loaded
        if self.targets:
            logging.debug("Proxy adapter with {:d} targets loaded".format(len(self.targets)))
        else:
            logging.error("Failed to resolve targets for proxy adapter")

        # Build the parameter trees implemented by this adapter for the specified proxy targets
        status_dict = {}
        tree = {}
        meta_tree = {}

        for target in self.targets:
            status_dict[target.name] = target.status_param_tree
            tree[target.name] = target.data_param_tree
            meta_tree[target.name] = target.meta_param_tree

        # Create a parameter tree from the status data for the targets and insert into the
        # data and metadata structures
        self.status_tree = ParameterTree(status_dict)
        tree["status"] = self.status_tree
        meta_tree["status"] = self.status_tree.get("", True)

        # Create the data and metadata parameter trees
        self.param_tree = ParameterTree(tree)
        self.meta_param_tree = ParameterTree(meta_tree)

    def proxy_get(self, path, get_metadata):
        """
        Get data from the proxy targets.

        This method gets data from one or more specified targets and returns the responses.

        :param path: path to data on remote targets
        :param get_metadata: flag indicating if metadata is to be requested
        :return: list of target responses
        """
        # Resolve the path element and target path
        path_elem, target_path = self._resolve_path(path)

        # Iterate over the targets and get data if the path matches
        target_responses = []
        for target in self.targets:
            if path_elem == "" or path_elem == target.name:
                target_responses.append(target.remote_get(target_path, get_metadata))

        return target_responses

    def proxy_set(self, path, data):
        """
        Set data on the proxy targets.

        This method sets data on one or more specified targets and returns the responses.

        :param path: path to data on remote targets
        :param data to set on targets
        :return: list of target responses
        """
        # Resolve the path element and target path
        path_elem, target_path = self._resolve_path(path)

        # Iterate over the targets and set data if the path matches
        target_responses = []
        for target in self.targets:
            if path_elem == "" or path_elem == target.name:
                target_responses.append(target.remote_set(target_path, data))

        return target_responses

    def _resolve_response(self, path, get_metadata=False):
        """
        Resolve the response to a proxy target get or set request.

        This method resolves the appropriate response to a proxy target get or set request. Data
        or metadata from the specified path is returned, along with an appropriate HTTP status code.

        :param path: path to data on remote targets
        :param get_metadata: flag indicating if metadata is to be requested

        """
        # Build the response from the adapter parameter trees, matching to the path for one or more
        # targets
        try:
            # If metadata is requested, update the status tree with metadata before returning
            # metadata
            if get_metadata:
                path_elem, _ = self._resolve_path(path)
                if path_elem in ("", "status"):
                    # update status tree with metadata
                    self.meta_param_tree.set("status", self.status_tree.get("", True))
                response = self.meta_param_tree.get(path)
            else:
                response = self.param_tree.get(path)
            status_code = 200
        except ParameterTreeError as param_tree_err:
            response = {"error": str(param_tree_err)}
            status_code = 400

        return (response, status_code)

    @staticmethod
    def _resolve_path(path):
        """
        Resolve the specified path into a path element and target.

        This method resolves the specified path into a path element and target path.

        :param path: path to data on remote targets
        :return: tuple of path element and target path
        """
        if "/" in path:
            path_elem, target_path = path.split("/", 1)
        else:
            path_elem = path
            target_path = ""
        return (path_elem, target_path)
