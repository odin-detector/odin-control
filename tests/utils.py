"""
Utility classes to support testing the ODIN framework

Tim Nicholls, STFC Application Engineering Group
"""

import sys
import time
import threading
import logging
import os

from tempfile import NamedTemporaryFile

if sys.version_info[0] == 3:  # pragma: no cover
    from configparser import ConfigParser
    import asyncio
else:                         # pragma: no cover
    from ConfigParser import SafeConfigParser as ConfigParser

from tornado.ioloop import IOLoop

from odin import main

def log_message_seen(caplog, level, message, when="call"):

    for record in caplog.get_records(when):
        if record.levelno == level and message in record.getMessage():
            return True

    return False


class OdinTestServer(object):

    server_port = 8888
    server_addr = '127.0.0.1'
    server_api_version = 0.1

    def __init__(
        self,
        server_port=server_port,
        adapter_config=None,
        access_logging=None,
        graylog_server=None,
        graylog_static_fields=None,
    ):

        self.server_thread = None
        self.server_event_loop = None

        self.server_conf_file = NamedTemporaryFile(mode='w+')
        parser = ConfigParser()

        file_dir = os.path.dirname(os.path.abspath(__file__))
        static_path = os.path.join(file_dir, 'static')

        parser.add_section('server')
        parser.set('server', 'debug_mode', '1')
        parser.set('server', 'http_port', str(server_port))
        parser.set('server', 'http_addr', self.server_addr)
        parser.set('server', 'static_path', static_path)

        if adapter_config is not None:
            adapters = ', '.join([adapter for adapter in adapter_config])
            parser.set('server', 'adapters', adapters)

        if access_logging is not None:
            parser.set("server", 'access_logging', access_logging)

        if graylog_server is not None:
            parser.set("server", 'graylog_server', graylog_server)
            if graylog_static_fields is not None:
                parser.set("server", 'graylog_static_fields', graylog_static_fields)

        parser.add_section('tornado')
        parser.set('tornado', 'logging', 'debug')

        if adapter_config is not None:
            for adapter in adapter_config:
                section_name = 'adapter.{}'.format(adapter)
                parser.add_section(section_name)
                for param in adapter_config[adapter]:
                    parser.set(section_name, param, str(adapter_config[adapter][param]))

        parser.write(self.server_conf_file)
        self.server_conf_file.file.flush()

        server_args = ['--config={}'.format(self.server_conf_file.name)]
        self.server_thread = threading.Thread(target=self._run_server, args=(server_args,))
        self.server_thread.start()
        time.sleep(0.2)

    def __del__(self):

        self.stop()

    def _run_server(self, server_args):
        if sys.version_info[0] == 3:  # pragma: no cover
            asyncio.set_event_loop(asyncio.new_event_loop())

        self.server_event_loop = IOLoop.current()
        main.main(server_args)

    def stop(self):

        if self.server_thread is not None:
            self.server_event_loop.add_callback(self.server_event_loop.stop)
            self.server_thread.join()
            self.server_thread = None

        if self.server_conf_file is not None:
            self.server_conf_file.close()

    def build_url(self, resource, api_version=None):
        if api_version is None:
            api_version = self.server_api_version
        return 'http://{}:{}/api/{}/{}'.format(
            self.server_addr, self.server_port,
            api_version, resource
        )
