import tornado.web

class DefaultHandler(tornado.web.RequestHandler):

    def get(self, path):
        self.write("Hello, world!\n")
        self.write("Requested path: {}\n".format(path))


DefaultRoute = (r"/(.*)", DefaultHandler)
