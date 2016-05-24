"""
test_plugin.py - end-to-end testing of the EXCALIBUR plugin in an ODIN server instance

Tim Nicholls, STFC Application Engineering Group
"""

from nose.tools import *

import requests
import json

from odin.testing.utils import OdinTestServer


class TestExcaliburPlugin(OdinTestServer):

    @classmethod
    def setup_class(cls):

        adapter_config = {
            'excalibur': {
                'module': 'excalibur.adapter.ExcaliburAdapter',
                'detector_fems': '192.168.0.1:6969, 192.168.0.2:6969, 192.168.0.3:6969',
            }
        }
        super(TestExcaliburPlugin, cls).setup_class(adapter_config)

    @classmethod
    def teardown_class(cls):
        super(TestExcaliburPlugin, cls).teardown_class()

    def test_simple_get(self):
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        result = requests.get(
            self.build_url('excalibur/config/none'),
            headers=headers
        )
        assert_equal(result.status_code, 200)
        assert_equal(result.json()['response'], 'ExcaliburAdapter: GET on path config/none')
