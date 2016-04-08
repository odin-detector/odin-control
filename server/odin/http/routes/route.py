class Route(object):

    def __init__(self):

        self.routes = []

    def add_to(self, routes=[]):

        routes.extend(self.routes)
        return routes
