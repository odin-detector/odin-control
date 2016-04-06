import fem_api

class ExcaliburFemError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class ExcaliburFem(object):

    def __init__(self, id):

        self.fem_handle = None
        try:
            self.fem_handle = fem_api.initialise(id)
        except fem_api.error as e:
            raise ExcaliburFemError(str(e))

    def close(self):

        try:
            fem_api.close(self.fem_handle)
        except fem_api.error as e:
            raise ExcaliburFemError(str(e))

    def get_id(self):

        return fem_api.get_id(self.fem_handle)

    def get_int(self, chip_id, param_id, size):

        return fem_api.get_int(self.fem_handle, chip_id, param_id, size)
