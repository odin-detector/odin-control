""" Unit tests for the ODIN SystemStatus adapter.

Tim Nicholls, STFC Application Engineering Group.
"""

import sys
import platform
import psutil
import logging

import pytest

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock, patch
else:                         # pragma: no cover
    from mock import Mock, patch

from odin.adapters.system_status import SystemStatusAdapter, SystemStatus, Singleton
from odin.adapters.parameter_tree import ParameterTreeError

from tests.utils import log_message_seen


class SystemStatusTestFixture():
    """Container class used in fixtures for testing the SystemStatus class."""

    def __init__(self, scoped_patcher):
        """Initialise a SystemStatus instance with an appropriate configuration."""
        if platform.system() == 'Darwin':
            self.lo_iface = 'lo0'
        else:
            self.lo_iface = 'lo'

        self.interfaces = "{}, bad".format(self.lo_iface)
        self.disks = "/, /bad"
        self.rate = 0.001

        self.mocked_proc_name = "mock_proc"
        self.processes = ", ".join([self.mocked_proc_name, "proc2"])

        self.mocked_procs = []
        self.parent_process = 1
        self.child_process = 0
        self.cpu_affinity_vals = [1, 2, 3]

        for idx, (name, cmdline) in enumerate(
            [
                (self.mocked_proc_name, "one two"),
                (self.mocked_proc_name, "four five"),
                ("bash", self.mocked_proc_name + " etc"),
            ]
        ):
            proc = Mock()
            proc.pid = 1000 + idx
            proc.name.return_value = name
            proc.cmdline.return_value = cmdline.split()
            proc.cpu_percent.return_value = 1.23
            if idx == self.parent_process:
                proc.children.return_value = [self.mocked_procs[self.child_process]]
            else:
                proc.children.return_value = None
            if idx > 0:
                proc.cpu_affinity.return_value = self.cpu_affinity_vals
            else:
                delattr(proc, 'cpu_affinity')
            proc.status.return_value = psutil.STATUS_RUNNING

            self.mocked_procs.append(proc)

        self.num_mocked_procs = len(self.mocked_procs)

        def mock_process_iter(attrs=None, ad_value=None):

            procs_to_yield = min(self.num_mocked_procs, len(self.mocked_procs))

            for proc in self.mocked_procs[:procs_to_yield]:
                yield proc

        scoped_patcher.setattr(psutil, "process_iter", mock_process_iter)

        self.system_status = SystemStatus(
            interfaces=self.interfaces, disks=self.disks, processes=self.processes, rate=self.rate)


#@pytest.fixture(scope="class")
@pytest.fixture()
def test_system_status():
    """Fixture used in SystemStatus test cases."""

    # Create a class-scoped monkey patcher to be used in the main fixture
    from _pytest.monkeypatch import MonkeyPatch
    scoped_patcher = MonkeyPatch()

    # Create the test fixture and yield to the tests
    test_system_status = SystemStatusTestFixture(scoped_patcher)
    yield test_system_status

    # Undo the patcher
    scoped_patcher.undo()

class TestSystemStatus():
    """Test cases for the SystemStatus class."""

    def test_system_status_single_instance(self, test_system_status):
        """Test that the SystemStatus class exhibits singleton behaviour."""
        new_instance = SystemStatus()
        assert test_system_status.system_status == new_instance

    def test_system_status_rate(self, test_system_status):
        """Test that the status update interval is calculated from the rate correctly. """
        update_interval = 1.0 / test_system_status.rate
        assert pytest.approx(update_interval) == test_system_status.system_status._update_interval

    def test_system_status_get(self, test_system_status):
        """Test that a GET call to SystemStatus returns a dict."""
        result = test_system_status.system_status.get('')
        assert type(result) is dict

    def test_system_status_add_processes(self, test_system_status):
        """Test that adding a process to SystemStatus works correctly."""
        test_system_status.system_status.add_processes('proc1')
        assert 'proc1' in test_system_status.system_status._processes

    def test_system_status_check_bad_nic(self, test_system_status):
        """
        Test that trying to get the status of a non-existing networking interface raises an error.
        """
        with pytest.raises(ParameterTreeError):
            test_system_status.system_status.get('status/network/bad')

    def test_system_status_monitor_network(self, test_system_status):
        """Test that getting the status of a network interface returns a dict."""
        test_system_status.system_status.monitor_network()
        result = test_system_status.system_status.get(
            'status/network/{}'.format(test_system_status.lo_iface))
        assert type(result) is dict

    def test_system_status_monitor_disks(self, test_system_status):
        """Test that getting the status of a system disk returns a dict."""
        test_system_status.system_status.monitor_disks()
        result = test_system_status.system_status.get('status/disk/_')
        assert type(result) is dict

    def test_system_status_monitor_processes(self, test_system_status):
        """Test that getting the status of a process returns a dict."""
        test_system_status.system_status.monitor_processes()
        result = test_system_status.system_status.get('status/process/proc2')
        assert type(result) is dict

    def test_system_status_monitor(self, test_system_status):
        test_system_status.num_mocked_procs = 2
        """Test that monitoring the status of the system does not raise an exception."""
        test_system_status.system_status.monitor()

    def test_bad_disk_exception(self, test_system_status):
        """Test that trying to monitor a bad disk does not raise an exception."""
        test_system_status.system_status._disks.append("rubbish")
        # Any exceptions caught whilst monitoring will be handled within the class
        test_system_status.system_status.monitor_disks()

    def test_bad_interface_exception(self, test_system_status):
        """Test that trying to monitor a bad network interface does not raise an exception."""
        test_system_status.system_status._interfaces.append("rubbish")
        # Any exceptions caught whilst monitoring will be handled within the class
        test_system_status.system_status.monitor_network()

    def test_bad_process_exception(self, test_system_status):
        """Test that trying to montiro a bad process does no raise an exception."""
        test_system_status.system_status._processes["rubbish"] = []
        # Any exceptions caught whilst monitoring will be handled within the class
        test_system_status.system_status.monitor_processes()

    def test_add_process_exception(self, test_system_status):
        """Test that trying to add a missing process does not raise an exception."""
        test_system_status.stash_method = test_system_status.system_status.find_processes
        test_system_status.system_status.find_processes = Mock(side_effect=KeyError('error'))
        # Any exceptions caught whilst adding processes will be handled within the class
        test_system_status.system_status.add_processes("process")
        test_system_status.system_status.find_processes = test_system_status.stash_method

    def test_update_loop_exception(self, test_system_status):
        """Test that monitoring the system in the update loop does not raise an exception."""
        test_system_status.stash_method = test_system_status.system_status.monitor
        test_system_status.system_status.monitor = Mock(side_effect=Exception('error'))
        # Any exceptions caught whilst monitoring will be handled within the class
        test_system_status.system_status.update_loop()
        test_system_status.system_status.monitor = test_system_status.stash_method

    def test_default_rate_argument(self, test_system_status):
        """Test that that the default monitoring rate argument is applied correctly."""
        stash_singleton = dict(Singleton._instances)
        Singleton._instances = {}
        temp_system_status = SystemStatus(
            interfaces=test_system_status.interfaces,
            disks=test_system_status.disks,
            processes=test_system_status.processes,
        )
        assert pytest.approx(1.0) == temp_system_status._update_interval
        Singleton._instances = {}
        Singleton._instances = dict(stash_singleton)

    def test_num_processes_change(self, test_system_status, caplog):
        """Test that monitoring processes correctly detects a change in the number of processes."""

        # Ensure that the process monitoring has run once
        test_system_status.system_status.monitor_processes()

        # Reduce the number of processes to find and monitor again -
        test_system_status.num_mocked_procs -= 1
        logging.getLogger().setLevel(logging.DEBUG)
        test_system_status.system_status.monitor_processes()

        # monitor_process will detect change in number of processes and log a debug message
        assert log_message_seen(
            caplog, logging.DEBUG, "Number of processes named mock_proc is now")

    def test_find_processes_handles_children(self, test_system_status):
        """Test that process monitoring correctly handles child processes."""
        mocked_procs = test_system_status.system_status._processes[
            test_system_status.mocked_proc_name]
        assert mocked_procs[test_system_status.parent_process] \
            == mocked_procs[test_system_status.child_process]

    def test_find_processes_matches_cmdline(self, test_system_status):
        """Test that finding processes by name can match against the command line also."""
        num_procs_found = len(test_system_status.system_status.find_processes_by_name(
            test_system_status.mocked_proc_name
        ))
        assert num_procs_found == test_system_status.num_mocked_procs

    def test_monitor_process_cpu_affinity(self, test_system_status, monkeypatch):
        """Test that monitoring processes reports CPU affinity where implemented."""

        test_system_status.system_status.monitor_processes()
        cpu_affinity_vals = [status['cpu_affinity'] for status in
            test_system_status.system_status._process_status[
                test_system_status.mocked_proc_name
            ].values()
        ]
        assert test_system_status.cpu_affinity_vals in cpu_affinity_vals

    def test_monitor_process_no_cpu_affinity(self, test_system_status, monkeypatch):
        """Test that monitoring processes handles systems without CPU affinity support."""
        try:
            monkeypatch.delattr(psutil.Process, 'cpu_affinity')
        except AttributeError:
            pass
        test_system_status.system_status.monitor_processes()

        test_system_status.system_status.monitor_processes()
        cpu_affinity_vals = [status['cpu_affinity'] for status in
            test_system_status.system_status._process_status[
                test_system_status.mocked_proc_name
            ].values()
        ]
        assert None in cpu_affinity_vals

    def test_monitor_process_traps_nosuchprocess(self, test_system_status):
        """Test that monitoring processes can cope with processing disappearing."""
        test_system_status.mocked_procs[0].memory_info.side_effect = psutil.NoSuchProcess('')
        test_system_status.system_status.monitor_processes()

    def test_monitor_process_traps_accessdenied(self, test_system_status):
        """Test that monitoring processes can cope with being denied access to process info."""
        test_system_status.mocked_procs[0].memory_info.side_effect = psutil.AccessDenied('')
        test_system_status.system_status.monitor_processes()

    def test_find_processes_traps_accessdenied(self, test_system_status):
        """Test that finding processes can cope with being denied access to process info."""
        for proc in test_system_status.mocked_procs:
            proc.cpu_percent.side_effect = psutil.AccessDenied('')
        processes = test_system_status.system_status.find_processes(
            test_system_status.mocked_proc_name
        )
        # If all processes are AccessDenied then the returned list will be empty
        assert not processes

    @pytest.mark.parametrize(
        "test_exc", [psutil.AccessDenied, psutil.ZombieProcess, psutil.NoSuchProcess]
    )
    def test_find_processes_by_name_traps_exceptions(self, test_system_status, test_exc):
        """Test the finding processes by name traps various psutil exception cases."""
        for proc in test_system_status.mocked_procs:
            proc.name.side_effect = test_exc('')
        processes = test_system_status.system_status.find_processes_by_name(
            test_system_status.mocked_proc_name
        )
        # If all process lookups result in an exception, the returned list will be empty
        assert not processes


class SystemStatusAdapterTestFixture():
    """Container class used in fixtures for testing SystemStatusAdapter."""

    def __init__(self):

        self.adapter = SystemStatusAdapter()
        self.path = ''
        self.request = Mock()
        self.request.headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}


@pytest.fixture(scope="class")
def test_sysstatus_adapter():
    """Fixture used in testing the SystemStatusAdapter class."""
    test_sysstatus_adapter = SystemStatusAdapterTestFixture()
    yield test_sysstatus_adapter


class TestSystemStatusAdapter():
    """Test cases for the SystemStatusAdapter class."""

    def test_adapter_get(self, test_sysstatus_adapter):
        """Test that a GET call to the adapter returns the appropriate response."""
        response = test_sysstatus_adapter.adapter.get(
            test_sysstatus_adapter.path, test_sysstatus_adapter.request)

        assert type(response.data) == dict
        assert 'status' in response.data
        assert response.status_code == 200

    def test_adapter_get_bad_path(self, test_sysstatus_adapter):
        """Test that GET call to the adapter with a bad path returns the appropriate error."""
        bad_path = '/bad/path'
        expected_response = {'error': 'Invalid path: {}'.format(bad_path)}

        response = test_sysstatus_adapter.adapter.get(bad_path, test_sysstatus_adapter.request)

        assert response.data == expected_response
        assert response.status_code == 400

    def test_adapter_put(self, test_sysstatus_adapter):
        """Test that a PUT call to the adapter returns the appropriate response."""
        expected_response = {
            'response': 'SystemStatusAdapter: PUT on path {}'.format(test_sysstatus_adapter.path)
        }

        response = test_sysstatus_adapter.adapter.put(
            test_sysstatus_adapter.path, test_sysstatus_adapter.request)

        assert response.data == expected_response
        assert response.status_code == 200

    def test_adapter_delete(self, test_sysstatus_adapter):
        """Test that a DELETE call to the adapter returns the appropriate response."""
        response = test_sysstatus_adapter.adapter.delete(
            test_sysstatus_adapter.path, test_sysstatus_adapter.request)

        assert response.data == 'SystemStatusAdapter: DELETE on path {}'.format(
            test_sysstatus_adapter.path)
        assert response.status_code == 200

    def test_adapter_put_bad_content_type(self, test_sysstatus_adapter):
        """Test that a PUT call with a bad content type returns the appropriate 415 error."""
        bad_request = Mock()
        bad_request.headers = {'Content-Type': 'text/plain'}

        response = test_sysstatus_adapter.adapter.put(test_sysstatus_adapter.path, bad_request)

        assert response.data == 'Request content type (text/plain) not supported'
        assert response.status_code == 415

    def test_adapter_put_bad_accept_type(self, test_sysstatus_adapter):
        """Test that a PUT call with a accept type returns the appropriate 406 error."""
        bad_request = Mock()
        bad_request.headers = {'Accept': 'text/plain'}
        response = test_sysstatus_adapter.adapter.put(test_sysstatus_adapter.path, bad_request)
        assert response.data == 'Requested content types not supported'
        assert response.status_code == 406
