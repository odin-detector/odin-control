from fem.client import ExcaliburFem, ExcaliburFemError
from nose.tools import *

class TestExcaliburFem:

    def test_legal_fem_id(self):

        id = 1234
        the_fem = ExcaliburFem(id)
        assert_equal(id, the_fem.get_id())

    def test_illegal_fem_id(self):

        id = -1
        with assert_raises(ExcaliburFemError) as cm:
            the_fem = ExcaliburFem(id)
        assert_equal(cm.exception.value, 'Error trying to initialise FEM id -1: Illegal ID specified')

    def test_double_close(self):

        the_fem = ExcaliburFem(0)
        the_fem.close()
        with assert_raises(ExcaliburFemError) as cm:
            the_fem.close()
        assert_equal(cm.exception.value, '_close: FEM object pointer has null FEM handle')
