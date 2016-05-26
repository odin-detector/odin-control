"""
test_adapter.py - test cases for the ExcaliburAdapter API adapter class for the ODIN server

Tim Nicholls, STFC Application Engineering Group
"""

import sys
from nose.tools import *

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock
else:                         # pragma: no cover
    from mock import Mock

from excalibur.adapter import ExcaliburAdapter

class ExcaliburAdapterFixture(object):

    @classmethod
    def setup_class(cls, **adapter_params):
        cls.adapter = ExcaliburAdapter(**adapter_params)
        cls.path = 'test/path'
        cls.request = Mock()
        cls.request.headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}


class TestExcaliburAdapter(ExcaliburAdapterFixture):

    @classmethod
    def setup_class(cls):

        adapter_params = {
            'detector_fems': '192.168.0.1:6969, 192.168.0.2:6969, 192.168.0.3:6969',
        }
        super(TestExcaliburAdapter, cls).setup_class(**adapter_params)

    def test_adapter_name(self):

        assert_equal(self.adapter.name, 'ExcaliburAdapter')

    def test_adapter_single_fem(self):
        adapter_params = {'detector_fems': '192.168.0.1:6969'}
        adapter = ExcaliburAdapter(**adapter_params)
        assert_equal(len(adapter.detector.fems), 1)

    def test_adapter_bad_fem_config(self):
        adapter_params = {'detector_fems': '192.168.0.1 6969, 192.168.0.2:6969'}
        adapter = ExcaliburAdapter(**adapter_params)
        assert_equal(adapter.detector, None)

    def test_adapter_get(self):
        expected_response = {'response': '{}: GET on path {}'.format(self.adapter.name, self.path)}
        response = self.adapter.get(self.path, self.request)
        assert_equal(response.data, expected_response)
        assert_equal(response.status_code, 200)

    def test_adapter_put(self):
        expected_response = {'response': '{}: PUT on path {}'.format(self.adapter.name, self.path)}
        response = self.adapter.put(self.path, self.request)
        assert_equal(response.data, expected_response)
        assert_equal(response.status_code, 200)

    def test_adapter_bad_path(self):
        response = self.adapter.put('bad_path', self.request)
        assert_equal(response.status_code, 400)

    def test_adapter_delete(self):
        expected_response = {
            'response': '{}: DELETE on path {}'.format(self.adapter.name, self.path)
        }
        response = self.adapter.delete(self.path, self.request)
        assert_equal(response.data, expected_response)
        assert_equal(response.status_code, 200)


class TestExcaliburAdapterNoFems(ExcaliburAdapterFixture):

    @classmethod
    def setup_class(cls):
        super(TestExcaliburAdapterNoFems, cls).setup_class()

    def test_adapter_no_fems(self):
        assert_equal(self.adapter.detector, None)

    def test_adapter_no_fems_get(self):
        response = self.adapter.get(self.path, self.request)
        assert_equal(response.status_code, 500)
