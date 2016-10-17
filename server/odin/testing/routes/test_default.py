"""
Test cases for oding.http.routes.default DefaultRoute class.

Tim Nicholls, STFC Application Engineering
"""
from nose.tools import *
import logging
import re

from odin.http.routes.default import DefaultRoute
from odin.testing.utils import LogCaptureFilter


class TestDefaultRoute():
    """Test DefaultRoute class."""

    @classmethod
    def setup_class(cls):
        """Set up class with a logging capture filter."""
        cls.log_capture_filter = LogCaptureFilter()

    def test_default_route_relative_path(self):
        """Test DefaultRoute resolves relative path for static content."""
        path = '.'
        def_route = DefaultRoute(path)
        assert_regexp_matches(def_route.default_handler_args['path'], 'server/odin')

    def test_default_route_absolute_path(self):
        """Test DefaultRoute treats absolute path for static content correctly."""
        path = '/absolute/path'
        def_route = DefaultRoute(path)
        assert_regexp_matches(def_route.default_handler_args['path'], path)

    def test_default_route_bad_path(self):
        """Test DefaultRoute logs warning about bad path to static content."""
        path = '../missing_path'
        def_route = DefaultRoute(path)
        assert_regexp_matches(def_route.default_handler_args['path'], 'missing_path')

        missing_path_msg_seen = False
        for msg in self.log_capture_filter.log_warning():
            if re.match('Default handler static path does not exist', msg):
                missing_path_msg_seen = True

        assert_true(missing_path_msg_seen)
