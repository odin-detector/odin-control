"""Monitoring of disk, network and process statistics running on a server.

Example config file section for odin-control:

[adapter.status]
module = odin_control.adapters.system_status.SystemStatusAdapter
disks = /home/gnx91527
interfaces = p3p1, p3p2
processes = stFrameProcessor1.sh, stFrameProcessor3.sh


disks is a comma separated list of disk mounts to monitor.  "/" is replaced with "_" for
indexing the values.
interfaces is a comma separated list of network interfaces to monitor.
processes in a comma separated list of processes to monitor.  Monitoring includes CPU and
memory use.

Created on 20 June 2018

Alan Greer, OSL
"""
import logging
import os

import psutil
from tornado.ioloop import IOLoop

from odin_control._version import __version__
from odin_control.adapters.adapter import ApiAdapter
from odin_control.adapters.base_controller import BaseController
from odin_control.adapters.parameter_tree import ParameterTree, ParameterTreeError


class SystemStatusController(BaseController):
    """Class to monitor disks, network and processes running on a server."""
    def __init__(self, *args, **kwargs):
        """Initalise the Server Monitor.

        Creates the parameter tree for status and process monitoring.
        """
        self._log = logging.getLogger(".".join([__name__, self.__class__.__name__]))
        self._processes = {}
        self._process_status = {}
        self._interfaces = []
        self._interface_status = {}
        self._disks = []
        self._disk_status = {}

        # The parameter tree will contain general server information as well as information
        # relating to each process.  We need to initialise the top level tree
        tree = {
            'status': {
                'disk': (self.get_disk_status, None),
                'network': (self.get_interface_status, None),
                'process': (self.get_process_status, None)
            }
        }

        # Add any disks that we need to monitor
        if 'disks' in kwargs:
            disks = kwargs['disks'].split(',')
            for disk in disks:
                if os.path.isdir(disk.strip()):
                    self._disks.append(disk.strip())

        for disk in self._disks:
            self._disk_status[disk.replace("/", "_")] = {
                'total': None,
                'used': None,
                'free': None,
                'percent': None
            }

        # Add any network interfaces that we need to monitor
        available_interfaces = list(psutil.net_io_counters(pernic=True))
        if 'interfaces' in kwargs:
            interfaces = kwargs['interfaces'].split(',')
            for interface in interfaces:
                if interface.strip() in available_interfaces:
                    self._interfaces.append(interface.strip())

        for interface in self._interfaces:
            self._interface_status[interface] = {
                'bytes_sent': None,
                'bytes_recv': None,
                'packets_sent': None,
                'packets_recv': None,
                'errin': None,
                'errout': None,
                'dropin': None,
                'dropout': None
            }

        # Add any processes that we need to monitor
        if 'processes' in kwargs:
            processes = kwargs['processes'].split(',')
            for process in processes:
                self.add_processes(process.strip())

        for process in self._processes:
            self._process_status[process] = {}

        self._status = ParameterTree(tree)

        # Setup the time between status updates
        if 'rate' in kwargs:
            self._update_interval = float(1.0 / kwargs['rate'])
        else:
            self._update_interval = 1.0
        self.update_loop()

    def get_disk_status(self):
        """Return disk status information."""
        return self._disk_status

    def get_interface_status(self):
        """Return network status information."""
        return self._interface_status

    def get_process_status(self):
        """Return process status information."""
        return self._process_status

    def get(self, path, with_metadata=False):
        """Return the requested path value."""
        return self._status.get(path, with_metadata=with_metadata)

    def update_loop(self):
        """Handle update loop tasks.

        This method handles background update tasks executed periodically in the tornado
        IOLoop instance. This includes monitoring all status from the server.
        """
        try:
            self.monitor()
        except Exception as exc:
            # Nothing to do here except log the error
            self._log.exception(exc)

        # Schedule the update loop to run in the IOLoop instance again after appropriate interval
        IOLoop.instance().call_later(self._update_interval, self.update_loop)

    def add_processes(self, process_name):
        """Add a new process to monitor.

        :param process_name the name of the process to monitor
        """
        if process_name not in self._processes:
            self._log.debug("Adding process %s to monitor list", process_name)
            try:
                self._processes[process_name] = self.find_processes(process_name)
                self._log.debug(
                    "Found %d proceses with name %s",
                    len(self._processes[process_name]), process_name
                )

            except Exception as exc:
                self._log.debug(
                    "Unable to add process %s to the monitor list: %s",
                    process_name, str(exc)
                )

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
                path = str(disk.replace("/", "_"))
                self._disk_status[path]['total'] = usage.total
                self._disk_status[path]['used'] = usage.used
                self._disk_status[path]['free'] = usage.free
                self._disk_status[path]['percent'] = usage.percent
            except Exception as exc:
                self._log.exception(exc)

    def monitor_network(self):
        """Loops over interfaces and retrieves the usage statistics."""
        try:
            network = psutil.net_io_counters(pernic=True)
            for interface in self._interfaces:
                self._interface_status[interface]['bytes_sent'] = network[interface].bytes_sent
                self._interface_status[interface]['bytes_recv'] = network[interface].bytes_recv
                self._interface_status[interface]['packets_sent'] = network[interface].packets_sent
                self._interface_status[interface]['packets_recv'] = network[interface].packets_recv
                self._interface_status[interface]['errin'] = network[interface].errin
                self._interface_status[interface]['errout'] = network[interface].errout
                self._interface_status[interface]['dropin'] = network[interface].dropin
                self._interface_status[interface]['dropout'] = network[interface].dropout
        except Exception as exc:
            self._log.exception(exc)

    def monitor_processes(self):
        """Loop over active processes and retrieves the statistics from them."""
        for process_name in self._processes:

            self._process_status[process_name] = {}

            num_processes_old = len(self._processes[process_name])
            self._processes[process_name] = self.find_processes(process_name)
            if len(self._processes[process_name]) != num_processes_old:
                self._log.debug(
                    "Number of processes named %s is now %d",
                    process_name, len(self._processes[process_name])
                )

            for process in self._processes[process_name]:
                process_status = {}
                try:
                    pid = process.pid
                    memory_info = process.memory_info()

                    process_status['cpu_percent'] = process.cpu_percent(interval=0.0)
                    if hasattr(process, 'cpu_affinity'):
                        process_status['cpu_affinity'] = process.cpu_affinity()
                    else:
                        process_status['cpu_affinity'] = None
                    process_status['memory_percent'] = process.memory_percent()

                    process_status['memory_rss'] = getattr(
                        memory_info, 'rss', None
                    )
                    process_status['memory_vms'] = getattr(
                        memory_info, 'vms', None
                    )
                    process_status['memory_shared'] = getattr(
                        memory_info, 'shared', None
                    )

                except psutil.NoSuchProcess:
                    self._log.error("Process %s no longer exists", process_name)
                except psutil.AccessDenied:
                    self._log.error("Access to process %s denied by operating system", process_name)
                else:
                    self._process_status[process_name][pid] = process_status

    def find_processes(self, process_name):
        """Find processes matching a name and return a list of process objects.

        Returns a list of psutil process object
        """
        processes = []

        parents = self.find_processes_by_name(process_name)
        for parent in parents:
            if parent.children():
                process = parent.children()[0]
            else:
                process = parent

            # Attempt to access process and remove if access denied
            try:
                _ = process.cpu_percent()
            except psutil.AccessDenied:
                pass
            else:
                processes.append(process)

        return processes

    def find_processes_by_name(self, name):
        """Find processes by name.

        Returns a list of process matching 'name' that is not this process (in the case
        where the process name was passed as an argument to this process).
        """
        processes = []
        for proc in psutil.process_iter():
            process = None
            try:
                if name in proc.name():
                    process = proc
                else:
                    for cmdline in proc.cmdline():
                        if name in cmdline:
                            # Make sure the name isn't found as an argument to this process!
                            if os.getpid() != proc.pid:
                                process = proc
            except (psutil.AccessDenied, psutil.ZombieProcess, psutil.NoSuchProcess):
                # If we cannot access the info of this process or it is a zombie or no longer
                # exists, move on
                pass

            if process is not None:
                if process.status() not in (
                        psutil.STATUS_ZOMBIE, psutil.STATUS_STOPPED, psutil.STATUS_DEAD
                ):
                    processes.append(process)

        return processes

class SystemStatusAdapter(ApiAdapter):
    """System status adapter class for the ODIN server.

    This adapter provides ODIN clients with information about the server disks, network
    and processes.
    """

    version = __version__
    controller_cls = SystemStatusController
    error_cls = ParameterTreeError
