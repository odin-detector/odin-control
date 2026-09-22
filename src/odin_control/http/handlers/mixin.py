"""Shared request-handler mixin for odin-control.

This module implements a mixin class providing CORS and Server header behaviour used by both API and
static route handlers.

Tim Nicholls, STFC Detector Systems Software Group
"""

from odin_control._version import __version__


class HandlerMixin:
    """Mixin to apply CORS and Server header behaviour to handlers."""

    def initialize(self, *args, **kwargs):
        """Initialise handler and set CORS headers if enabled.

        Expects optional ``enable_cors`` and ``cors_origin`` keyword arguments in
        handler URLSpec params.
        """
        enable_cors = kwargs.pop("enable_cors", False)
        cors_origin = kwargs.pop("cors_origin", "*")

        super().initialize(*args, **kwargs)  # type: ignore[misc]

        if enable_cors:
            self.set_header("Access-Control-Allow-Origin", cors_origin)
            self.set_header("Access-Control-Allow-Headers", "x-requested-with,content-type")
            self.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")

    def options(self, *_):
        """Handle CORS preflight OPTIONS requests with no content."""
        self.set_status(204)

    def set_default_headers(self):
        """Set default response headers including an OdinControl Server token.

        This method overrides the base RequestHandler to set the default Server header for all
        responses. The header is set to include name and version of odin-control. If the header is
        already set, e.g. by the base Tornado implementation, append that value to the header.
        """
        server_header_str = f"OdinControl/{__version__}"
        if "Server" in self._headers and not str(self._headers["Server"]).startswith(
            server_header_str
        ):
            server_header_str += f" {self._headers['Server']}"

        self.set_header("Server", server_header_str)
