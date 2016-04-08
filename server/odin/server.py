from odin.http.server import HttpServer

import logging
import signal
import threading

import tornado.ioloop
import tornado.options
from tornado.options import options

def sigint_handler(signum, frame):
    logging.info("Interrupt signal received, shutting down")
    tornado.ioloop.IOLoop.instance().stop()

def main():

    # Define configuration options and add to tornado option parser
    tornado.options.define("http_addr", default="0.0.0.0", help="Set HTTP server address")
    tornado.options.define("http_port", default=8888, help="Set HTTP server port")
    tornado.options.define("debug_mode", default=False, help="Enable tornado debug mode")

    # Parse the command line options
    tornado.options.parse_command_line()

    # Launch the HTTP server
    http_server = HttpServer(options.debug_mode)
    http_server.listen(options.http_port, options.http_addr)

    logging.info("HTTP server listening on {}:{}" .format(options.http_addr, options.http_port))

    # Register a SIGINT signal handler only if this is the main thread
    if isinstance(threading.current_thread(), threading._MainThread):
        signal.signal(signal.SIGINT, sigint_handler)

    # Enter IO processing loop
    tornado.ioloop.IOLoop.instance().start()

    logging.info("ODIN server shutdown")

if __name__ == "__main__":
    main()
