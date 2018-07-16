import sys

from nose.tools import *

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock
else:                         # pragma: no cover
    from mock import Mock

from odin.adapters.system_status import SystemStatusAdapter, SystemStatus
from odin.adapters.parameter_tree import ParameterTreeError

class TestSystemStatus():

    @classmethod
    def setup_class(cls):

        cls.system_status = SystemStatus(interfaces="lo, bad", disks="/, /bad", processes='python, proc2', rate=0.001)

    def test_system_status_single_instance(self):
        new_instance = SystemStatus()
        assert_equal(self.system_status, new_instance)

    def test_system_status_rate(self):
        assert_almost_equal(1000.0, self.system_status._update_interval)

    def test_system_status_get(self):
        result = self.system_status.get('')
        assert_equal(type(result), dict)

    def test_system_status_add_process(self):
        self.system_status.add_process('proc1')
        assert_true('proc1' in self.system_status._processes)

    def test_system_status_check_bad_nic(self):
        with assert_raises(KeyError):
            self.system_status.get('status/network/bad')

    def test_system_status_monitor_network(self):
        self.system_status.monitor_network()
        result = self.system_status.get('status/network/lo')
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
        try:
            self.system_status.monitor()
        except:
            self.fail("SystemStatus.monitor raised an unexpected Exception")


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
