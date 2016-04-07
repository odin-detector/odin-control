import os

import tornado.web

class DefaultHandler(tornado.web.RequestHandler):

    def get(self):
        self.redirect("/static/index.html")


DefaultRoute = (r"/", DefaultHandler)
