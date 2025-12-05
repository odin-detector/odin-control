"""System info adapter class for the ODIN server.

This class implements a system information adapter for the ODIN server, providing system-level
information about the system to clients.

Tim Nicholls, STFC Application Engineering
"""
import platform
import time

import tornado

from odin_control._version import __version__
from odin_control.adapters.adapter import ApiAdapter
from odin_control.adapters.base_controller import BaseController
from odin_control.adapters.parameter_tree import ParameterTree, ParameterTreeError


class SystemInfoController(BaseController):
    """SystemInfoController class that extracts and stores system-level parameters."""

    def __init__(self, options=None):
        """Initialise the SystemInfo object.

        This constructor initlialises the SystemInfo object, extracting various system-level
        parameters and storing them in a parameter tree to be accessible to clients.
        """
        # Store initialisation time
        self.init_time = time.time()

        # Extract platform information and store in parameter tree
        (system, node, release, version, _, processor) = platform.uname()
        platform_tree = ParameterTree({
            'name': 'platform',
            'description': "Information about the underlying platform",
            'system': (lambda: system, {
                "name": "system",
                "description": "operating system name",
            }),
            'node': (lambda: node, {
                "name": "node",
                "description": "node (host) name",
            }),
            'release': (lambda: release, {
                "name": "release",
                "description": "operating system release",
            }),
            'version': (lambda: version, {
                "name": "version",
                "description": "operating system version",
            }),
            'processor': (lambda: processor, {
                "name": "processor",
                "description": "processor (CPU) name",
            }),
        })

        # Store all information in a parameter tree
        self.param_tree = ParameterTree({
            'name': 'system_info',
            'description': 'Information about the system hosting this odin server instance',
            'odin_version': (lambda: __version__, {
                "name": "odin version",
                "description": "ODIN server version",
            }),
            'tornado_version': (lambda: tornado.version, {
                "name": "tornado version",
                "description": "version of tornado used in this server",
            }),
            'python_version': (lambda: platform.python_version(), {
                "name": "python version",
                "description": "version of python running this server",
            }),
            'platform': platform_tree,
            'server_uptime': (self.get_server_uptime, {
                "name": "server uptime",
                "description": "time since the ODIN server started",
                "units": "s",
                "display_precision": 2,
            }),
        })

    def get_server_uptime(self):
        """Get the uptime for the ODIN server.

        This method returns the current uptime for the ODIN server.
        """
        return time.time() - self.init_time

    def get(self, path, with_metadata=False):
        """Get the parameter tree.

        This method returns the parameter tree for use by clients via the SystemInfo adapter.

        :param path: path to retrieve from tree
        """
        return self.param_tree.get(path, with_metadata)

class SystemInfoAdapter(ApiAdapter):
    """System info adapter class for the ODIN server.

    This adapter provides ODIN clients with information about the server and the system that it is
    running on.
    """

    version = __version__
    controller_cls = SystemInfoController
    error_cls = ParameterTreeError
