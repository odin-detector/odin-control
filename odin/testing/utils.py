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
    from configparser import SafeConfigParser
    import asyncio
else:                         # pragma: no cover
    from ConfigParser import SafeConfigParser

from tornado.ioloop import IOLoop

from odin import server


class LogCaptureFilter(logging.Filter):

    def __init__(self, *args, **kwargs):

        logging.Filter.__init__(self, *args, **kwargs)
        self.messages = {logging.DEBUG: [],
                         logging.INFO: [],
                         logging.WARNING: [],
                         logging.ERROR: [],
                         logging.CRITICAL: []
                         }

        root_logger = logging.getLogger()
        if len(root_logger.handlers) == 0:
            root_logger.addHandler(logging.handlers.MemoryHandler(100))  # pragma: nocover

        root_logger.handlers[0].addFilter(self)

        for level in self.messages:
            msg_getter_name = 'log_{}'.format(logging.getLevelName(level).lower())
            setattr(self, msg_getter_name, lambda self=self, level=level: self.messages[level])

    def filter(self, record):

        self.messages[record.levelno].append(record.getMessage())
        return True


class OdinTestServer(object):

    launch_server = True
    server_host = 'localhost'
    server_port = 8888
    server_api_version = 0.1
    server_event_loop = None
    server_thread = None
    server_conf_file = None

    @classmethod
    def start_server(cls, adapter_config=None, access_logging=None):

        cls.server_conf_file = NamedTemporaryFile(mode='w+')
        parser = SafeConfigParser()

        file_dir = os.path.dirname(os.path.abspath(__file__))
        static_path = os.path.join(file_dir, 'static')

        parser.add_section('server')
        parser.set('server', 'debug_mode', '1')
        parser.set('server', 'http_port', str(cls.server_port))
        parser.set('server', 'http_addr', '127.0.0.1')
        parser.set('server', 'static_path', static_path)
        
        if adapter_config is not None:
            adapters = ', '.join([adapter for adapter in adapter_config])
            parser.set('server', 'adapters', adapters)

        if access_logging is not None:
            parser.set("server", 'access_logging', 'debug')

        parser.add_section('tornado')
        parser.set('tornado', 'logging', 'debug')

        if adapter_config is not None:
            for adapter in adapter_config:
                section_name = 'adapter.{}'.format(adapter)
                parser.add_section(section_name)
                for param in adapter_config[adapter]:
                    parser.set(section_name, param, str(adapter_config[adapter][param]))

        parser.write(cls.server_conf_file)
        cls.server_conf_file.file.flush()

        server_args = ['--config={}'.format(cls.server_conf_file.name)]

        cls.server_thread = threading.Thread(target=cls.run_server, args=(server_args,))
        cls.server_thread.start()

    @classmethod
    def run_server(cls, server_args):

        if sys.version_info[0] == 3:  # pragma: no cover
            asyncio.set_event_loop(asyncio.new_event_loop())

        cls.server_event_loop = IOLoop.current()
        server.main(server_args)

    @classmethod
    def stop_server(cls):
        if cls.server_thread is not None:
            cls.server_event_loop.add_callback(cls.server_event_loop.stop)
            cls.server_thread.join()
            cls.server_thread = None

        if cls.server_conf_file is not None:
            cls.server_conf_file.close()
            cls.server_conf_file = None

    @classmethod
    def setup_class(cls, adapter_config=None, access_logging=None):
        if cls.launch_server:
            cls.log_capture_filter = LogCaptureFilter()
            cls.start_server(adapter_config, access_logging)
            time.sleep(0.2)

    @classmethod
    def teardown_class(cls):
        if cls.launch_server:
            cls.stop_server()

    def build_url(self, resource, api_version=None):
        if api_version is None:
            api_version = self.server_api_version
        return 'http://{}:{}/api/{}/{}'.format(
            self.server_host, self.server_port,
            api_version, resource
        )
