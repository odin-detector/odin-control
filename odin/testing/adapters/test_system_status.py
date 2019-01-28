import sys
import platform
from nose.tools import *
import psutil

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock, patch
else:                         # pragma: no cover
    from mock import Mock, patch

from odin.adapters.system_status import SystemStatusAdapter, SystemStatus, Singleton
from odin.adapters.parameter_tree import ParameterTreeError

class TestSystemStatus():

    @classmethod
    def setup_class(cls):

        if platform.system() == 'Darwin':
            cls.lo_iface='lo0'
        else:
            cls.lo_iface='lo'
            
        cls.interfaces="{}, bad".format(cls.lo_iface)
        cls.disks = "/, /bad"
        cls.processes = "python, proc2"
        cls.rate = 0.001

        cls.system_status = SystemStatus(
            interfaces=cls.interfaces, disks=cls.disks, processes=cls.processes, rate=cls.rate)

    def test_system_status_single_instance(self):
        new_instance = SystemStatus()
        assert_equal(self.system_status, new_instance)

    def test_system_status_rate(self):
        assert_almost_equal(1000.0, self.system_status._update_interval)

    def test_system_status_get(self):
        result = self.system_status.get('')
        assert_equal(type(result), dict)

    def test_system_status_add_processes(self):
        self.system_status.add_processes('proc1')
        assert_true('proc1' in self.system_status._processes)

    def test_system_status_check_bad_nic(self):
        with assert_raises(KeyError):
            self.system_status.get('status/network/bad')

    def test_system_status_monitor_network(self):
        self.system_status.monitor_network()
        result = self.system_status.get('status/network/{}'.format(self.lo_iface))
        assert_equal(type(result), dict)

    def test_system_status_monitor_disks(self):
        self.system_status.monitor_disks()
        result = self.system_status.get('status/disk/_')
        assert_equal(type(result), dict)

    def test_system_status_monitor_processes(self):
        self.system_status.monitor_processes()
        result = self.system_status.get('status/process/proc2')
        assert_equal(type(result), dict)

    def test_system_status_monitor(self):
        self.system_status.monitor()

    def test_bad_disk_exception(self):
        self.system_status._disks.append("rubbish")
        # Any exceptions caught whilst monitoring will be handled within the class
        self.system_status.monitor_disks()

    def test_bad_interface_exception(self):
        self.system_status._interfaces.append("rubbish")
        # Any exceptions caught whilst monitoring will be handled within the class
        self.system_status.monitor_network()

    def test_bad_process_exception(self):
        self.system_status._processes["rubbish"] = []
        # Any exceptions caught whilst monitoring will be handled within the class
        self.system_status.monitor_processes()

    def test_add_process_exception(self):
        self.stash_method = self.system_status.find_processes
        self.system_status.find_processes = Mock(side_effect=KeyError('error'))
        # Any exceptions caught whilst adding processes will be handled within the class
        self.system_status.add_processes("process")
        self.system_status.find_processes = self.stash_method

    def test_update_loop_exception(self):
        self.stash_method = self.system_status.monitor
        self.system_status.monitor = Mock(side_effect=Exception('error'))
        # Any exceptions caught whilst monitoring will be handled within the class
        self.system_status.update_loop()
        self.system_status.monitor = self.stash_method

    def test_default_rate_argument(self):

        stash_singleton = dict(Singleton._instances)
        Singleton._instances = {}
        temp_system_status = SystemStatus(
            interfaces=self.interfaces, disks=self.disks, processes=self.processes,
        )
        assert_almost_equal(1.0, temp_system_status._update_interval)
        Singleton._instances = {}
        Singleton._instances = dict(stash_singleton)

    def test_num_processes_change(self):

        self.stash_method = self.system_status.find_processes
        self.stash_processes = dict(self.system_status._processes)
        self.system_status._processes = {}
        self.system_status._processes['python'] = self.stash_processes['python']
        current_processes = self.system_status.find_processes('python')
        patched_processes = list(current_processes)
        patched_processes.append(current_processes[0])

        self.system_status.find_processes = Mock(return_value = patched_processes)
        self.system_status.monitor_processes()
        # monitor_process will detect change in number of processes
        self.system_status.find_processes = self.stash_method
        self.system_status._processes = self.stash_processes

    def test_monitor_process_cpu_affinity(self):

        self.stash_proc = self.system_status._processes['python'][0]

        setattr(self.system_status._processes['python'][0], 'cpu_affinity', lambda: [1,2,3])
        self.system_status.monitor_processes()

        delattr(self.system_status._processes['python'][0], 'cpu_affinity')
        self.system_status.monitor_processes()

        self.system_status._processes['python'][0] = self.stash_proc

    def test_monitor_process_traps_nosuchprocess(self):

        with patch('psutil.Process.memory_info', spec=True) as mocked:
            mocked.side_effect = psutil.NoSuchProcess('')
            self.system_status.monitor_processes()

    def test_monitor_process_traps_accessdenied(self):

        with patch('psutil.Process.memory_info', spec=True) as mocked:
            mocked.side_effect = psutil.AccessDenied('')
            self.system_status.monitor_processes()
        
    def test_find_processes_traps_accessdenied(self):

        with patch('psutil.Process.cpu_percent', spec=True) as mocked:
            mocked.side_effect = psutil.AccessDenied('')
            processes = self.system_status.find_processes('python') 
            # If all processes are AccessDenied then the returned list will be empty
            assert_false(processes)
        

class TestSystemStatusAdapter():

    @classmethod
    def setup_class(cls):

        cls.adapter = SystemStatusAdapter()
        cls.path = ''
        cls.request = Mock()
        cls.request.headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    def test_adapter_get(self):
        response = self.adapter.get(self.path, self.request)

        assert_equal(type(response.data), dict)
        assert_true('status' in response.data)
        assert_equal(response.status_code, 200)

    def test_adapter_get_bad_path(self):
        bad_path = '/bad/path'
        expected_response = {'error': 'The path {} is invalid'.format(bad_path)}
        response = self.adapter.get(bad_path, self.request)
        assert_equal(response.data, expected_response)
        assert_equal(response.status_code, 400)

    def test_adapter_put(self):

        expected_response = {'response': 'SystemStatusAdapter: PUT on path {}'.format(self.path)}
        response = self.adapter.put(self.path, self.request)
        assert_equal(response.data, expected_response)
        assert_equal(response.status_code, 200)

    def test_adapter_delete(self):
        response = self.adapter.delete(self.path, self.request)
        assert_equal(response.data, 'SystemStatusAdapter: DELETE on path {}'.format(self.path))
        assert_equal(response.status_code, 200)

    def test_adapter_put_bad_content_type(self):
        bad_request = Mock()
        bad_request.headers = {'Content-Type': 'text/plain'}
        response = self.adapter.put(self.path, bad_request)
        assert_equal(response.data, 'Request content type (text/plain) not supported')
        assert_equal(response.status_code, 415)

    def test_adapter_put_bad_accept_type(self):
        bad_request = Mock()
        bad_request.headers = {'Accept': 'text/plain'}
        response = self.adapter.put(self.path, bad_request)
        assert_equal(response.data, 'Requested content types not supported')
        assert_equal(response.status_code, 406)
