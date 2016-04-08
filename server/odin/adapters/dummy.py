import logging
from odin.adapters.adapter import ApiAdapter

class DummyAdapter(ApiAdapter):

    def __init__(self):

        super(DummyAdapter, self).__init__()
        logging.debug("DummyAdapter loaded")

    def get(self, path):

        response = "DummyAdapter: GET on path {}".format(path)
        code = 200

        logging.debug(response)

        return(response, code)

    def put(self, path):

        response = "DummyAdapter: PUT on path {}".format(path)
        code = 200

        logging.debug(response)

        return(response, code)

    def delete(self, path):

        response = "DummyAdapter: DELETE on path {}".format(path)
        code = 200

        logging.debug(response)

        return(response, code)
