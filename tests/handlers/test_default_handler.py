"""Tests for the DefaultHandler class."""

from unittest.mock import Mock

import pytest

from odin_control._version import __version__
from odin_control.http.handlers.default import DefaultHandler


class TestDefaultHandler:
    """Test cases for the DefaultHandler class."""

    def test_server_header_includes_odincontrol_version(self):
        """Test DefaultHandler sets Server header including OdinControl version."""
        app = Mock()
        app.ui_methods = {}
        request = Mock()

        handler = DefaultHandler(app, request, path='.', default_filename='index.html')

        assert f"OdinControl/{__version__}" in handler._headers['Server']
        assert 'TornadoServer/' in handler._headers['Server']

    @pytest.mark.parametrize('enable_cors,cors_origin,expect_header', [
        (True, '*', True),
        (True, 'https://example.com', True),
        (False, '*', False),
    ])
    def test_cors_headers(self, enable_cors, cors_origin, expect_header):
        """Test DefaultHandler applies CORS headers according to configuration."""
        app = Mock()
        app.ui_methods = {}
        request = Mock()

        handler = DefaultHandler(
            app,
            request,
            path='.',
            default_filename='index.html',
            enable_cors=enable_cors,
            cors_origin=cors_origin,
        )

        if expect_header:
            assert handler._headers['Access-Control-Allow-Origin'] == cors_origin
            assert handler._headers['Access-Control-Allow-Headers'] == 'x-requested-with,content-type'
            assert handler._headers['Access-Control-Allow-Methods'] == 'GET, POST, PUT, DELETE, OPTIONS'
        else:
            assert 'Access-Control-Allow-Origin' not in handler._headers
