import json
import logging
import requests
import sys

import pytest
if sys.version_info[0] == 3:  # pragma: no cover
    from unittest import mock
else:                         # pragma: no cover
    import mock

from odin.http.server import HttpServer
from odin import main

from tests.utils import OdinTestServer, log_message_seen
from tests.ssl_utils import SslTestCert

@pytest.fixture(scope="class")
def odin_test_server():
    """Test fixture for starting an odin test server instance with a dummy adapter loaded."""
    adapter_config = {
        'dummy': {
            'module': 'odin.adapters.dummy.DummyAdapter',
            'background_task_enable': 1,
            'background_task_interval': 0.1,
        }
    }
    access_logging='debug'

    test_server = OdinTestServer(
        adapter_config=adapter_config, access_logging=access_logging
    )
    yield test_server
    test_server.stop()

class TestOdinServer(object):
    """Test basic operation of the odin server with a dummy adapter loaded."""

    def test_simple_client_get(self, odin_test_server):
        """Test that a simple GET request succeeds."""
        result = requests.get(odin_test_server.build_url('dummy/config/none'))
        assert result.status_code == 200

    def test_adapter_get_trailing_slash(self, odin_test_server):
        """Test that a simple GET with a trailing slash in the URL succeeds"""
        result = requests.get(odin_test_server.build_url('dummy/'))
        assert result.status_code == 200

    def test_adapter_get_no_trailing_slash(self, odin_test_server):
        """Test that a simple GET without a trailing slash in the URL succeeds"""
        result = requests.get(odin_test_server.build_url('dummy'))
        assert result.status_code == 200

    def test_simple_client_put(self, odin_test_server):
        """Test that a simple PUT request succeeds."""
        headers = {'Content-Type' : 'application/json'}
        payload = {'some': 'data'}
        result = requests.put(odin_test_server.build_url('dummy/command/execute'),
            data=json.dumps(payload),
            headers=headers)
        assert result.status_code == 200

    def test_simple_client_delete(self, odin_test_server):
        """Test that a simple DELETE request succeeds."""
        result = requests.delete(odin_test_server.build_url('dummy/object/delete'))
        assert result.status_code == 200

    def test_bad_api_version(self, odin_test_server):
        """Test that a mistatch in API version numbers returns an error."""
        bad_api_version = 99.9
        temp_api_version = odin_test_server.server_api_version
        odin_test_server.server_api_version = bad_api_version
        url = odin_test_server.build_url('dummy/bad/version')
        odin_test_server.server_api_version = temp_api_version
        result = requests.get(url)
        assert result.status_code == 400
        assert result.content.decode('utf-8') == 'API version {} is not supported'.format(bad_api_version)

    def test_bad_subsystem_adapter(self, odin_test_server):
        """Test the requesting a missing subsytem adapter returns an error and message."""
        missing_subsystem = 'missing'
        result = requests.get(odin_test_server.build_url('{}/object'.format(missing_subsystem)))
        assert result.status_code == 400
        assert result.content.decode('utf-8') == 'No API adapter registered for subsystem {}'.format(missing_subsystem)

    def test_api_version(self, odin_test_server):
        """Test that the server returns the appropriate API version."""
        headers = {'Accept' : 'application/json'}
        result = requests.get(
            'http://{}:{}/api'.format(odin_test_server.server_addr, odin_test_server.server_port),
            headers=headers
        )
        assert result.status_code == 200
        assert result.json()['api'] == odin_test_server.server_api_version

    def test_api_version_bad_accept(self, odin_test_server):
        """Test that bad accept heeader content type returns an error and message."""
        headers = {'Accept': 'text/plain'}
        result = requests.get(
            'http://{}:{}/api'.format(odin_test_server.server_addr, odin_test_server.server_port),
            headers=headers
        )
        assert result.status_code == 406
        assert result.text == 'Requested content types not supported'

    def test_api_adapter_list(self, odin_test_server):
        """Test that the API route returns a list of loaded adapters at the appropriate URL."""
        headers = {'Accept': 'application/json'}
        result = requests.get(odin_test_server.build_url('adapters/'), headers=headers)
        assert result.status_code == 200
        assert result.json()['adapters'] == ['dummy']

    def test_api_adapter_list_bad_version(self, odin_test_server):
        """Test that the API route rejects an adapter list GET with a bad API version."""
        result = requests.get(odin_test_server.build_url('adapters/', api_version='99.9'))
        assert result.status_code == 400

    def test_api_adapter_list_bad_accept(self, odin_test_server):
        """Test that the API route rejects and adapter list GET with a bad Accept type."""
        headers = {'Accept': 'test/plain'}
        result = requests.get(odin_test_server.build_url('adapters/'), headers=headers)
        assert result.status_code == 406

    def test_default_handler(self, odin_test_server):
        """Test that the default handler returns OK for the top-level URL."""
        result = requests.get("http://{}:{}".format(odin_test_server.server_addr, odin_test_server.server_port))
        assert result.status_code == 200

    def test_default_accept(self, odin_test_server):
        """Test that a default accept type works correctly for a top-level URL."""
        result = requests.get(
            'http://{}:{}/api'.format(odin_test_server.server_addr, odin_test_server.server_port),
        )
        assert result.status_code == 200

    def test_background_task_in_adapter(self, odin_test_server):
        """Test that a background task in an adapter functions."""
        result = requests.get(odin_test_server.build_url('dummy/background_task_count'))
        assert result.status_code == 200
        count = result.json()['response']['background_task_count']
        assert count > 0

def test_graylog_handler_pygelf():
    """Test that gelf handler is added if pygelf is available"""
    try:
        import pygelf
        del pygelf
    except ImportError:
        return  # Cannot test pygelf functionality

    with mock.patch.object(logging.getLogger(), "addHandler") as mock_add_handler, \
        mock.patch("pygelf.GelfUdpHandler") as mock_gelf:

        server = OdinTestServer(
            graylog_server="127.0.0.1:12210",
            graylog_static_fields="key1=val1,key2=val2"
        )
        server.stop()

        mock_add_handler.assert_called_with(mock_gelf.return_value)


def test_graylog_handler_no_pygelf(caplog):
    """Test that an error is logged if called without pygelf available"""
    with mock.patch.dict(sys.modules, {"pygelf": None}):
        server = OdinTestServer(graylog_server="127.0.0.1:12210")
        server.stop()

    assert log_message_seen(
        caplog,
        logging.ERROR,
        "Cannot add graylog handler - pygelf is not installed"
    )


class TestBadServerConfig(object):
    """Class for testing a server with a bad configuration argument."""

    def test_server_entry_config_error(self):
        """Test that starting a server with a bad config fail raturns an error."""
        server_args = ['--config=absent.cfg']
        rc = main.main((server_args),)
        assert rc == 2

class ServerConfig():
    """Simple class for creating a dummy parsed server configuration."""
    def __init__(self):
        self.enable_http = True
        self.enable_https = False
        self.http_addr = '127.0.0.1'
        self.http_port = 8888
        self.https_port = 8443
        self.ssl_cert_file = 'cert.pem'
        self.ssl_key_file = 'key.pem'
        self.debug_mode = False
        self.log_function = None
        self.static_path = "./static"
        self.adapters = []
        self.access_logging = None
        self.enable_cors = True
        self.cors_origin = "*"

    def resolve_adapters(self):
        return []

@pytest.fixture()
def server_config():
    """Test fixture yielding a dummy parsed server configuration."""
    yield ServerConfig()

class TestOdinServerAccessLogging():
    """Class for testing a bad access logging level congiguration."""
    def test_bad_access_log_level(self, server_config, caplog):
        """Test that a bad access logging level generates an error."""
        bad_level  = 'wibble'
        server_config.access_logging = bad_level
        http_server = HttpServer(server_config)
        http_server.stop()

        assert log_message_seen(caplog, logging.ERROR,
            'Access logging level {} not recognised'.format(bad_level))

@pytest.fixture(scope="class")
def no_adapter_server():
    """Test fixture for starting a test server with no adapters loaded."""
    test_server = OdinTestServer(server_port=8889)
    yield test_server
    test_server.stop()

class TestOdinServerMissingAdapters(object):
    """Class to test a server with no adapters loaded."""

    def test_server_missing_adapters(self, no_adapter_server, caplog):
        """Test that a server with no adapters loaded generates a warning message."""
        assert log_message_seen(caplog, logging.WARNING,
            'Failed to resolve API adapters: No adapters specified in configuration',
            when="setup")

class TestOdinServerListenFailed(object):

    def test_http_server_listen_fails(self, caplog):

        config_1 = ServerConfig()
        config_2 = ServerConfig()

        server1 = HttpServer(config_1)
        server2 = HttpServer(config_2)

        server1.stop()
        server2.stop()

        assert log_message_seen(caplog, logging.ERROR, "Address already in use")

class MockHandler(object):
    """Class for mocking tornado request handler objects."""

    class Request(object):
        """Inner class mocking the request being handled."""

        def __init__(self, request_time=0):
            """Initialise request with a request_time field."""
            self._request_time = request_time

        def request_time(self):
            """Return the request time."""
            return self._request_time

    def __init__(self, status=200, summary=None, request_time=0):
        """Initialise the mock handler with appropriate fields."""
        self.status = status
        self.summary = summary
        self.request = MockHandler.Request(request_time)

    def get_status(self):
        """Return the mocked request status."""
        return self.status

    def _request_summary(self):
        """Return the mocked request summary."""
        return self.summary

class LoggingTestServer(object):
    """
    Class that starts an odin HTTPServer instance and allows its log output to be checked
    via the pytest capture log mechanism.
    """

    def __init__(self, caplog):
        """Initialise the logging test server."""
        self.http_server = HttpServer(ServerConfig())
        self.request_summary = 'request'
        self.request_time = 1234
        self.caplog = caplog

    def do_log_request(self, http_status, level):
        """
        Generate a mock request handler and verify that the logger generates the
        appropriate message.
        """
        handler = MockHandler(http_status, self.request_summary, self.request_time)
        self.http_server.log_request(handler)

        msg_seen = False
        for record in self.caplog.records:
            if record.levelno == level and record.getMessage() == '{:d} {:s} {:.2f}ms'.format(
                    http_status, self.request_summary, self.request_time*1000.0):
                msg_seen = True
        return msg_seen

    def __del__(self):
        self.http_server.stop()

@pytest.fixture()
def logging_test_server(caplog):
    """
    Test fixture for starting a logging test server. Note this has function scope rather than
    class, as the pytest caplog fixture only has function scope.
    """
    test_server = LoggingTestServer(caplog)
    yield test_server

class TestOdinHttpServerLogging(object):
    """Class for testing server logging."""

    def test_success_logging(self, logging_test_server):
        """Test that successful requests log at debug level."""
        assert logging_test_server.do_log_request(200, logging.DEBUG)

    def test_warning_logging(self, logging_test_server):
        """Test that 'not found' requests log at warning level."""
        assert logging_test_server.do_log_request(404, logging.WARNING)

    def test_error_logging(self, logging_test_server):
        """Test that failing requests log at error level."""
        assert logging_test_server.do_log_request(503, logging.ERROR)

class HttpsTestServer():

    def __init__(self, caplog):

        self.server_config = ServerConfig()
        self.server_config.enable_https = True
        self.https_server = HttpServer(self.server_config)
        self.caplog = caplog

    def __del__(self):
        self.https_server.stop()

@pytest.fixture()
def https_test_server(caplog):
    """
    Test fixture for starting a logging test server with HTTPS enabled
    """
    test_server = HttpsTestServer(caplog)
    yield test_server

@pytest.fixture(scope='class')
def ssl_test_cert():

    test_cert = SslTestCert()
    yield test_cert

class TestOdinHttpsServer():

    def test_https_valid_config(self, server_config, ssl_test_cert, caplog):

        server_config.enable_https = True
        server_config.ssl_cert_file = ssl_test_cert.cert_file 
        server_config.ssl_key_file = ssl_test_cert.key_file 
        server = HttpServer(server_config)
        server.stop()

        assert log_message_seen(
            caplog, logging.INFO,
            "HTTPS server listening on {}:{}".format(
                server_config.http_addr, server_config.https_port
            )
        )

    def test_https_no_ssl_files(self, server_config, caplog):
        server_config.enable_https = True
        server = HttpServer(server_config)
        server.stop()
        assert log_message_seen(
            caplog, logging.ERROR,
            "Failed to create SSL context for HTTPS: [Errno 2] No such file or directory",
        )

    def test_https_listen_error(self, server_config, ssl_test_cert, caplog):

        server_config.enable_https = True
        server_config.ssl_cert_file = ssl_test_cert.cert_file
        server_config.ssl_key_file = ssl_test_cert.key_file
        server_config.https_port = 443
        server = HttpServer(server_config)
        server.stop()

        assert log_message_seen(
            caplog, logging.ERROR,
            "Failed to create HTTPS server on {}:{}: [Errno 13] Permission denied".format(
                server_config.http_addr, server_config.https_port,
            )
        )