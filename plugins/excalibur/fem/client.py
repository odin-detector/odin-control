import fem_api

class ExcaliburFemError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class ExcaliburFem(object):

    FEM_RTN_OK = 0
    FEM_RTN_UNKNOWNOPID = 1
    FEM_RTN_ILLEGALCHIP = 2
    FEM_RTN_BADSIZE = 3
    FEM_RTN_INITFAILED = 4

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

    def cmd(self, chip_id, cmd_id):

        rc = ExcaliburFem.FEM_RTN_OK
        try:
            rc = fem_api.cmd(self.fem_handle, chip_id, cmd_id)
        except fem_api.error as e:
            raise ExcaliburFemError(str(e))

        return rc
