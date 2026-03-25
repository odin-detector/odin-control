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
from dataclasses import dataclass, fields

import psutil
from tornado.ioloop import IOLoop

from odin_control._version import __version__
from odin_control.adapters.adapter import ApiAdapter
from odin_control.adapters.base_controller import BaseController
from odin_control.adapters.parameter_tree import ParameterTree, ParameterTreeError


class ParameterTreeMixin:
    """Mixin class to provide ParameterTree functionality to dataclasses."""

    def __iter__(self):
        """Generate an iterator over the field names in the dataclass."""
        for field in fields(self):
            yield field.name

    def as_tree(self):
        """Return a ParameterTree representation of the dataclass."""
        return ParameterTree({
            name: (lambda name=name: getattr(self, name), None) for name in self
        })

@dataclass
class DiskStatus(ParameterTreeMixin):
    """Dataclass to hold disk status information."""
    total: int = 0
    used: int = 0
    free: int = 0
    percent: float = 0.0

@dataclass
class InterfaceStatus(ParameterTreeMixin):
    """Dataclass to hold network interface status information."""
    bytes_sent: int = 0
    bytes_recv: int = 0
    packets_sent: int = 0
    packets_recv: int = 0
    errin: int = 0
    errout: int = 0
    dropin: int = 0
    dropout: int = 0

@dataclass
class ProcessStatus(ParameterTreeMixin):
    """Dataclass to hold process status information."""
    cpu_percent: float = 0.0
    cpu_affinity: list = None
    memory_percent: float = 0.0
    memory_rss: int = 0
    memory_vms: int = 0
    memory_shared: int = 0


class SystemStatusController(BaseController):
    """Class to monitor disks, network and processes running on a server."""

    def __init__(self, options=None):
        """Initalise the Server Monitor.

        Creates the parameter tree for status and process monitoring.
        """
        self._log = logging.getLogger(".".join([__name__, self.__class__.__name__]))
        self._disks = {}
        self._disk_status = {}
        self._disk_tree = {}
        self._interfaces = []
        self._interface_status = {}
        self._network_tree = {}
        self._processes = {}
        self._process_tree = {}

        # Add any disks that we need to monitor
        if 'disks' in options:
            self.add_disks(options['disks'].split(','))

        # Add any network interfaces that we need to monitor
        if 'interfaces' in options:
            self.add_interfaces(options['interfaces'].split(','))

        # Add any processes that we need to monitor
        if 'processes' in options:
            self.add_processes(options['processes'].split(','))

        # Setup the time between status updates
        if 'rate' in options:
            self._update_interval = float(1.0 / options['rate'])
        else:
            self._update_interval = 1.0

        # Build the parameter tree - this is mutable, allowing the process subtree to be replaced on
        # each monitoring update as the number of monitored processes can change
        self.param_tree = ParameterTree({
            'disk': self._disk_tree,
            'network': self._network_tree,
            'process': self._process_tree,
        }, mutable=True)

        # Start the update loop
        self.update_loop()

    def get(self, path, with_metadata=False):
        """Return the requested path value."""
        return self.param_tree.get(path, with_metadata=with_metadata)

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

    def add_disks(self, disks):
        """Add disks to monitor.

        :param disks: the disk mount points to monitor
        """
        for disk in disks:
            disk = disk.strip()
            if os.path.isdir(disk):

                path = disk.replace("/", "_")

                self._disks[path] = disk
                self._disk_status[path] = DiskStatus()
                self._disk_tree[path] = self._disk_status[path].as_tree()

                logging.debug("Adding disk %s to monitor list", disk)

    def add_interfaces(self, interfaces):
        """Add a new network interface to monitor.

        :param interfaces: list of network interfaces to monitor
        """
        available_interfaces = list(psutil.net_io_counters(pernic=True))

        for interface in interfaces:
            interface = interface.strip()
            if interface in available_interfaces:
                self._interfaces.append(interface)
                self._interface_status[interface] = InterfaceStatus()
                self._network_tree[interface] = self._interface_status[interface].as_tree()

                logging.debug("Adding interface %s to monitor list", interface)

    def add_processes(self, processes):
        """Add a new process to monitor.

        :param processes: list of process names to monitor
        """
        for process_name in processes:
            process_name = process_name.strip()

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
        for path, disk in self._disks.items():
            try:
                usage = psutil.disk_usage(disk)
                for field in self._disk_status[path]:
                    setattr(self._disk_status[path], field, getattr(usage, field))

            except Exception as exc:
                self._log.exception(exc)

    def monitor_network(self):
        """Loops over interfaces and retrieves the usage statistics."""
        try:
            network = psutil.net_io_counters(pernic=True)
            for interface in self._interfaces:
                for field in self._interface_status[interface]:
                    setattr(
                        self._interface_status[interface],
                        field,
                        getattr(network[interface], field)
                    )
        except Exception as exc:
            self._log.exception(exc)

    def monitor_processes(self):
        """Loop over active processes and retrieves the statistics from them."""
        self._process_tree = {}

        for process_name in self._processes:

            self._process_tree[process_name] = {}

            num_processes_old = len(self._processes[process_name])
            self._processes[process_name] = self.find_processes(process_name)

            if len(self._processes[process_name]) != num_processes_old:
                self._log.debug(
                    "Number of processes named %s is now %d",
                    process_name, len(self._processes[process_name])
                )

            for process in self._processes[process_name]:
                process_status = ProcessStatus()
                try:
                    pid = process.pid
                    memory_info = process.memory_info()

                    process_status.cpu_percent = process.cpu_percent(interval=0.0)
                    if hasattr(process, 'cpu_affinity'):
                        process_status.cpu_affinity = process.cpu_affinity()
                    process_status.memory_percent = process.memory_percent()

                    process_status.memory_rss = getattr(memory_info, 'rss', None)
                    process_status.memory_vms = getattr(memory_info, 'vms', None)
                    process_status.memory_shared = getattr(memory_info, 'shared', None)

                except psutil.NoSuchProcess:
                    self._log.error("Process %s no longer exists", process_name)
                except psutil.AccessDenied:
                    self._log.error("Access to process %s denied by operating system", process_name)
                else:
                    self._process_tree[process_name][str(pid)] = process_status.as_tree()

        self.param_tree.replace('process', self._process_tree)


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
            except (psutil.AccessDenied, psutil.ZombieProcess, psutil.NoSuchProcess):
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
