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

class TestExcaliburAdapter():

    @classmethod
    def setup_class(cls):

        cls.adapter = ExcaliburAdapter()
        cls.path = '/excalibur/test/path'
        cls.request = Mock()
        cls.request.headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    def test_adapter_name(self):

        assert_equal(self.adapter.name, 'ExcaliburAdapter')

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


    def test_adapter_delete(self):
        expected_response = {'response': '{}: DELETE on path {}'.format(self.adapter.name, self.path)}
        response = self.adapter.delete(self.path, self.request)
        assert_equal(response.data, expected_response)
        assert_equal(response.status_code, 200)