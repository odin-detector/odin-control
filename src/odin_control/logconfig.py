import os
import sys
import logging
import getpass
from typing import Optional


def add_graylog_handler(
    log_server: str, log_level: int = logging.INFO, static_fields: Optional[str] = None
) -> None:
    """Add a graylog handler to the root logger

    Args:
        log_server: Graylog server endpoint, e.g. "127.0.0.1:12201"
        log_level: Log level to filter messages by in handler
        static_fields: Comma-separated string of extra fields to include in log message
            metadata, e.g. "_field1=value1,_field2=value2" (fields should have a
            leading underscore).
    """
    try:
        from pygelf import GelfUdpHandler
    except ImportError:
        logging.error("Cannot add graylog handler - pygelf is not installed")
        return

    host, port = log_server.split(":")
    config = {
        "host": host,
        "port": int(port),
        "debug": True,  # Include file, line, module, func, logger_name
        # Add custom fields
        "include_extra_fields": True,
        "_username": getpass.getuser(),
        "_process_id": os.getpid(),
        "_application_name": os.path.split(sys.argv[0])[1]
    }

    if static_fields is not None:
        static_fields = dict(entry.split("=") for entry in static_fields.split(","))
        config.update(static_fields)

    handler: logging.Handler = GelfUdpHandler(**config)
    handler.setLevel(log_level)
    logging.getLogger().addHandler(handler)
