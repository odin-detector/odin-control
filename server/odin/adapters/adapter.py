class ApiAdapter(object):
    """
    API adapter base class

    This class defines the basis for all API adapters and provides default
    methods for the required HTTP verbs in case the derived classes fail to
    implement them, returning an error message and 400 code.
    """

    def __init__(self):
        self.name = type(self).__name__
        pass

    def get(self, path):
        response = "GET method not implemented by {}".format(self.name)
        return(response, 400)

    def put(self, path):
        response = "PUT method not implemented by {}".format(self.name)
        return(response, 400)

    def delete(self, path):
        response = "DELETE method not implemented by {}".format(self.name)
        return(response, 400)
