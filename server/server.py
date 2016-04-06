import app.api_server

import logging
import signal

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

    # Launch the API server app
    api_server = app.api_server.ApiServer(options.debug_mode)
    api_server.listen(options.http_port, options.http_addr)

    logging.info("API HTTP server listening on {}:{}" .format(options.http_addr, options.http_port))

    # Register a SIGINT signal handler
    signal.signal(signal.SIGINT, sigint_handler)

    # Enter IO processing loop
    tornado.ioloop.IOLoop.instance().start()

    logging.info("ODIN server shutdown")

if __name__ == "__main__":
    main()
