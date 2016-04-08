import os
import tornado.web

from odin.http.routes.route import Route

class DefaultHandler(tornado.web.RequestHandler):

    def get(self):
        self.redirect("/static/index.html")

class DefaultRoute(Route):

    def __init__(self):

        self.add_handler((r"/", DefaultHandler))
