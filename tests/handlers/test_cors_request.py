"""Tests for the CorsRequestHandler class."""

from unittest.mock import Mock

import pytest

from odin_control.http.handlers.cors_request import CorsRequestHandler


class TestCorsRequestHandler:
    """Test cases for the CorsRequestHandler class."""

    @pytest.mark.parametrize("enable_cors,cors_origin", [
        (True, "*"),
        (True, "https://example.com"),
        (True, "https://localhost:8080"),
        (False, "*"),
        (False, "https://example.com"),
    ])
    def test_cors_configuration_combinations(self, enable_cors, cors_origin):
        """Test various combinations of CORS configuration parameters."""
        # Create mock objects
        app = Mock()
        app.ui_methods = {}
        request = Mock()
        route = Mock()

        # Create handler
        handler = CorsRequestHandler(
            app, request, route=route, enable_cors=enable_cors, cors_origin=cors_origin
        )

        # Check route is stored
        assert handler.route == route

        # Define expected CORS headers
        cors_headers = {
            "Access-Control-Allow-Origin": cors_origin,
            "Access-Control-Allow-Headers": "x-requested-with,content-type",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS"
        }

        if enable_cors:
            # Check that all CORS headers are set with correct values
            for header_name, expected_value in cors_headers.items():
                assert handler._headers[header_name] == expected_value
        else:
            # Check that no CORS headers are set
            for header_name in cors_headers.keys():
                assert header_name not in handler._headers

    @pytest.mark.parametrize("args", [
        (),  # No arguments
        ("subsystem", "path", "extra_arg"),  # Multiple arguments
    ], ids=["no_args", "with_args"])
    def test_options_request_handling(self, args):
        """Test that OPTIONS requests are handled correctly with various argument combinations."""
        # Create mock objects
        app = Mock()
        app.ui_methods = {}
        request = Mock()
        route = Mock()

        # Create handler
        handler = CorsRequestHandler(app, request, route=route, enable_cors=True, cors_origin="*")

        # Mock the set_status method to track calls
        handler.set_status = Mock()

        # Call options method (simulating OPTIONS request)
        handler.options(*args)

        # Check that status 204 (No Content) is set
        handler.set_status.assert_called_once_with(204)

