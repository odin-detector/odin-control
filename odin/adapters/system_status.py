"""Monitoring of disk, network and process statistics running on a server.

Example config file section for odin-control:

[adapter.status]
module = odin.adapters.system_status.SystemStatusAdapter
disks = /home/gnx91527
interfaces = p3p1, p3p2
processes = stFrameProcessor1.sh, stFrameProcessor3.sh


disks is a comma separated list of disk mounts to monitor.  "/" is replaced with "_" for indexing the values.
interfaces is a comma separated list of network interfaces to monitor.
processes in a comma separated list of processes to monitor.  Monitoring includes CPU and memory use.

Created on 20 June 2018

Alan Greer, OSL
"""
from __future__ import print_function

import logging
import os
import psutil
from future.utils import with_metaclass
from odin.adapters.adapter import ApiAdapter, ApiAdapterResponse, request_types, response_types
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from tornado.ioloop import IOLoop


class SystemStatusAdapter(ApiAdapter):
    """System status adapter class for the ODIN server.

    This adapter provides ODIN clients with information about the server disks, network
    and processes.
    """

    def __init__(self, **kwargs):
        """Initialize the SystemInfoAdapter object.

        This constructor initializes the SystemInfoAdapter object, including resolving any
        system-level information that the adapter can provide to clients subsequently.

        :param kwargs: keyword arguments specifying options
        """
        super(SystemStatusAdapter, self).__init__(**kwargs)
        self.system_status = SystemStatus(None, **kwargs)
        logging.debug('SystemStatusAdapter loaded')

    @response_types('application/json', default='application/json')
    def get(self, path, request):
        """Handle an HTTP GET request.

        This method handles an HTTP GET request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        response = {}
        try:
            response = self.system_status.get(path)
            status_code = 200
        except ParameterTreeError as e:
            response = {'error': str(e)}
            status_code = 400

        logging.debug(response)
        content_type = 'application/json'

        return ApiAdapterResponse(response, content_type=content_type,
                                  status_code=status_code)

    @request_types('application/json')
    @response_types('application/json', default='application/json')
    def put(self, path, request):
        """Handle an HTTP PUT request.

        This method handles an HTTP PUT request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        response = {'response': 'SystemStatusAdapter: PUT on path {}'.format(path)}
        content_type = 'application/json'
        status_code = 200

        logging.debug(response)

        return ApiAdapterResponse(response, content_type=content_type,
                                  status_code=status_code)

    def delete(self, path, request):
        """Handle an HTTP DELETE request.

        This method handles an HTTP DELETE request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        response = 'SystemStatusAdapter: DELETE on path {}'.format(path)
        status_code = 200

        logging.debug(response)

        return ApiAdapterResponse(response, status_code=status_code)


class Singleton(type):
    """Singleton metaclass for use with SystemMonitor to ensure only one instance is created."""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """Ensure only a single instance of any class is created."""
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class SystemStatus(with_metaclass(Singleton, object)):
    """Class to monitor disks, network and processes running on a server."""
    def __init__(self, *args, **kwargs):
        """Initalise the Server Monitor.

        Creates the parameter tree for status and process monitoring.
        """
        self._log = logging.getLogger(".".join([__name__, self.__class__.__name__]))
        self._processes = {}
        self._interfaces = []
        self._disks = []

        # The parameter tree will contain general server information as well as information
        # relating to each process.  We need to initialise the top level tree
        tree = {
            'status': {
                'disk': {},
                'network': {},
                'process': {}
            }
        }

        # Add any disks that we need to monitor
        if 'disks' in kwargs:
            disks = kwargs['disks'].split(',')
            for disk in disks:
                if os.path.isdir(disk.strip()):
                    self._disks.append(disk.strip())

        for disk in self._disks:
            tree['status']['disk'][disk.replace("/", "_")] = {
                'total': 0,
                'used': 0,
                'free': 0,
                'percent': 0.0
            }

        # Add any network interfaces that we need to monitor
        available_interfaces = list(psutil.net_io_counters(pernic=True))
        if 'interfaces' in kwargs:
            interfaces = kwargs['interfaces'].split(',')
            for interface in interfaces:
                if interface.strip() in available_interfaces:
                    self._interfaces.append(interface.strip())

        for interface in self._interfaces:
            tree['status']['network'][interface] = {
                'bytes_sent': 0,
                'bytes_recv': 0,
                'packets_sent': 0,
                'packets_recv': 0,
                'errin': 0,
                'errout': 0,
                'dropin': 0,
                'dropout': 0
            }

        # Add any processes that we need to monitor
        if 'processes' in kwargs:
            processes = kwargs['processes'].split(',')
            for process in processes:
                self.add_process(process.strip())

        for process in self._processes:
            tree['status']['process'][process] = {
                'cpu_percent': 0.0,
                'cpu_affinity': [],
                'memory_percent': 0.0,
                'memory_rss': 0,
                'memory_vms': 0,
                'memory_shared': 0
            }

        self._status = ParameterTree(tree)

        # Setup the time between status updates
        if 'rate' in kwargs:
            self._update_interval = float(1.0 / kwargs['rate'])
        else:
            self._update_interval = 1.0
        self.update_loop()

    def get(self, path):
        """Return the requested path value"""
        return self._status.get(path)

    def update_loop(self):
        """Handle update loop tasks.
        This method handles background update tasks executed periodically in the tornado
        IOLoop instance. This includes monitoring all status from the server.
        """
        try:
            self.monitor()
        except Exception as e:
            # Nothing to do here except log the error
            self._log.exception(e)

        # Schedule the update loop to run in the IOLoop instance again after appropriate interval
        IOLoop.instance().call_later(self._update_interval, self.update_loop)

    def add_process(self, process_name):
        """Add a new process to monitor.

        :param process_name the name of the process to monitor
        """
        if process_name not in self._processes:
            self._log.debug("Adding process %s to monitor list", process_name)
            self._processes[process_name] = self.find_process(process_name)

    def monitor(self):
        """Executed at regular interval.  Calls the specific monitoring methods."""
        self.monitor_disks()
        self.monitor_network()
        self.monitor_processes()

    def monitor_disks(self):
        """Loops over disks and retrieves the usage statistics."""
        for disk in self._disks:
            try:
                usage = psutil.disk_usage(disk)
                path = "status/disk/" + str(disk.replace("/", "_"))
                self._status.set(path + "/total", usage.total)
                self._status.set(path + "/used", usage.used)
                self._status.set(path + "/free", usage.free)
                self._status.set(path + "/percent", usage.percent)
            except Exception as e:
                self._log.exception(e)

    def monitor_network(self):
        """Loops over interfaces and retrieves the usage statistics."""
        try:
            network = psutil.net_io_counters(pernic=True)
            for interface in self._interfaces:
                if interface in network:
                    path = "status/network/" + interface
                    self._status.set(path + "/bytes_sent", network[interface].bytes_sent)
                    self._status.set(path + "/bytes_recv", network[interface].bytes_recv)
                    self._status.set(path + "/packets_sent", network[interface].packets_sent)
                    self._status.set(path + "/packets_recv", network[interface].packets_recv)
                    self._status.set(path + "/errin", network[interface].errin)
                    self._status.set(path + "/errout", network[interface].errout)
                    self._status.set(path + "/dropin", network[interface].dropin)
                    self._status.set(path + "/dropout", network[interface].dropout)
        except Exception as e:
            self._log.exception(e)

    def monitor_processes(self):
        """Loops over active processes and retrieves the statistics from them."""
        for process_name in self._processes:
            try:
                if self._processes[process_name] is None:
                    self._processes[process_name] = self.find_process(process_name)

                process = self._processes[process_name]
                if process is not None:
                    memory_info = process.memory_info()
                    path = "status/process/" + process_name
                    self._status.set(path + "/cpu_percent", process.cpu_percent(interval=0.0))
                    self._status.set(path + "/cpu_affinity", process.cpu_affinity())
                    self._status.set(path + "/memory_percent", process.memory_percent())
                    self._status.set(path + "/memory_rss", memory_info.rss)
                    self._status.set(path + "/memory_vms", memory_info.vms)
                    self._status.set(path + "/memory_shared", memory_info.shared)
            except:
                # Any exception may occur due to the process not existing etc, so reset the process object
                self._processes[process_name] = None

    def find_process(self, process_name):
        """Find a process and return the process object.

        Returns a psutil process object
        """
        parent = self.find_process_by_name(process_name)
        if parent is not None:
            if len(parent.children()) > 0:
                process = parent.children()[0]
            else:
                process = parent
        else:
            process = None
        return process

    def find_process_by_name(self, name):
        """Return the first process matching 'name' that is not this process (in the case
        where the process name was passed as an argument to this process)."""
        proc = None
        for p in psutil.process_iter():
            if name in p.name():
                self._log.debug("Found %s in %s", name, p.name())
                proc = p
            else:
                for cmdline in p.cmdline():
                    if name in cmdline:
                        # Make sure the name isn't found as an argument to this process!
                        if os.getpid() != p.pid:
                            self._log.debug("Found %s in %s", name, p.cmdline())
                            proc = p
        if proc is not None:
            if proc.status == psutil.STATUS_ZOMBIE \
                or proc.status == psutil.STATUS_STOPPED \
                or proc.status == psutil.STATUS_DEAD:
                proc = None
        return proc
