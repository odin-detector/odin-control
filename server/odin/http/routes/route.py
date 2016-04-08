class Route(object):

    """
    Base class for server routes

    This class defines a simple container that can be initialised with
    URLspec-formatted handlers, i.e. tuples containing a URL pattern
    and an associated RequestHandler subclass to be invoked
    """

    def __init__(self):

        # Initialise empty list of handlers
        self.handlers = []

    def add_handler(self, handler):

        """
        Add a handler to the route, The handler should be a URLspec-formatted
        tuple, i.e. (<pattern>, <handler>)
        """

        if not hasattr(self, 'handlers'):
            self.handlers = []
        self.handlers.append(handler)

    def get_handlers(self):

        """
        Returns a list of handlers

        This method returns a list of handlers currently present
        in the Route object.
        """

        return self.handlers if hasattr(self, 'handlers') else []
