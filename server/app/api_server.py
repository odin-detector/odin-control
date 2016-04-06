import os
import time
import json

import tornado.gen
import tornado.web
import tornado.ioloop

import logging

class MainHandler(tornado.web.RequestHandler):

    def get(self):
        self.write("Hello, world!")

class ApiHandler(tornado.web.RequestHandler):

    def get(self, path):
        self.write("API GET on path {}\n".format(path))

class ApiServer(object):

    def __init__(self, debug_mode=False):

        settings = {
            "static_path": os.path.abspath(os.path.join(os.path.dirname(__file__), "../static")),
            "debug" : debug_mode,
            }

        self.application = tornado.web.Application([
            (r"/", MainHandler),
            (r"/api/(.*)", ApiHandler),
        ], **settings)

    def listen(self, port, host=''):

        self.application.listen(port, host)
