import sys
import json

import pytest

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock
else:                         # pragma: no cover
    from mock import Mock

from odin.http.handlers.base import BaseApiHandler, API_VERSION
from tests.handlers.api_test_handler import test_api_handler

class TestBaseApiHandler(object):

    def test_handler_valid_get(self, test_api_handler):
        test_api_handler.handler.get(str(API_VERSION),
            test_api_handler.subsystem, test_api_handler.path)



