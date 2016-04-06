from fem.client import ExcaliburFem, ExcaliburFemError
from nose.tools import *

class TestExcaliburFem:

    @classmethod
    def setup_class(cls):
        cls.fem_id = 1234
        cls.the_fem = ExcaliburFem(cls.fem_id)

    def test_legal_fem_id(self):

        assert_equal(self.fem_id, self.the_fem.get_id())

    def test_illegal_fem_id(self):

        id = -1
        with assert_raises(ExcaliburFemError) as cm:
            bad_fem = ExcaliburFem(id)
        assert_equal(cm.exception.value, 'Error trying to initialise FEM id {}: Illegal ID specified'.format(id))

    def test_double_close(self):

        the_fem = ExcaliburFem(0)
        the_fem.close()
        with assert_raises(ExcaliburFemError) as cm:
            the_fem.close()
        assert_equal(cm.exception.value, '_close: FEM object pointer has null FEM handle')

    def test_legal_get_int(self):

        chip_id = 0
        param_id = 1001
        param_len = 10
        (rc, values) = self.the_fem.get_int(chip_id, param_id, param_len)

        assert_equal(rc, ExcaliburFem.FEM_RTN_OK)
        assert_equal(len(values), param_len)
        assert_equal(values, tuple(range(param_id, param_id+param_len)))

    def test_legal_cmd(self):

        chip_id = 0
        cmd_id = 1
        rc = self.the_fem.cmd(chip_id, cmd_id)
        assert_equal(rc, ExcaliburFem.FEM_RTN_OK)

    def test_illegal_cmd(self):

        chip_id  = 0;
        cmd_id = -1
        rc = self.the_fem.cmd(chip_id, cmd_id)
        assert_equal(rc, ExcaliburFem.FEM_RTN_UNKNOWNOPID)
