""" Test ParameterTree class.

Tim Nicholls, STFC Application Engingeering
"""

from copy import deepcopy

import pytest

from odin.adapters.parameter_tree import ParameterAccessor, ParameterTree, ParameterTreeError


class ParameterAccessorTestFixture(object):
    """Container class used in fixtures for testing ParameterAccessor."""
    def __init__(self):

        self.static_rw_path = 'static_rw'
        self.static_rw_value = 2.76923
        self.static_rw_accessor = ParameterAccessor(self.static_rw_path + '/', self.static_rw_value)

        self.callable_ro_value = 1234
        self.callable_ro_path = 'callable_ro'
        self.callable_ro_accessor = ParameterAccessor(self.callable_ro_path + '/', self.callable_ro_get)

        self.callable_rw_value = 'foo'
        self.callable_rw_path = 'callable_rw'
        self.callable_rw_accessor = ParameterAccessor(
            self.callable_rw_path + '/', self.callable_rw_get, self.callable_rw_set)

        self.md_param_path ='mdparam'
        self.md_param_val = 456
        self.md_param_metadata = {
            'min' : 100,
            'max' : 1000,
            "allowed_values": [100, 123, 456, 789, 1000],
            "name": "Test Parameter",
            "description": "This is a test parameter",
            "units": "furlongs/fortnight",
            "display_precision": 0,
        }
        self.md_accessor = ParameterAccessor(
            self.md_param_path + '/', self.md_param_val, **self.md_param_metadata
        )

        self.md_minmax_path = 'minmaxparam'
        self.md_minmax_val = 500
        self.md_minmax_metadata = {
            'min': 100,
            'max': 1000
        }
        self.md_minmax_accessor = ParameterAccessor(
            self.md_minmax_path + '/', self.md_minmax_val, **self.md_minmax_metadata
        )

    def callable_ro_get(self):
        return self.callable_ro_value

    def callable_rw_get(self):
        return self.callable_rw_value

    def callable_rw_set(self, value):
        self.callable_rw_value = value


@pytest.fixture(scope="class")
def test_param_accessor():
    """Test fixture used in testing ParameterAccessor behaviour."""
    test_param_accessor = ParameterAccessorTestFixture()
    yield test_param_accessor


class TestParameterAccessor():
    """Class to test ParameterAccessor behaviour."""

    def test_static_rw_accessor_get(self, test_param_accessor):
        """Test that a static RW accessor get call returns the correct value."""
        assert test_param_accessor.static_rw_accessor.get() == test_param_accessor.static_rw_value

    def test_static_rw_accessor_set(self, test_param_accessor):
        """Test that a static RW accessor set call sets the correct value."""
        old_val = test_param_accessor.static_rw_value
        new_val = 1.234
        test_param_accessor.static_rw_accessor.set(new_val)
        assert test_param_accessor.static_rw_accessor.get() == new_val

        test_param_accessor.static_rw_accessor.set(old_val)

    def test_callable_ro_accessor_get(self, test_param_accessor):
        """Test that a callable RO accessor get call returns the correct value."""
        assert test_param_accessor.callable_ro_accessor.get() == \
            test_param_accessor.callable_ro_value

    def test_callable_ro_accessor_set(self, test_param_accessor):
        """Test that a callable RO accessor set call raises an error."""
        new_val = 91265
        with pytest.raises(ParameterTreeError) as excinfo:
            test_param_accessor.callable_ro_accessor.set(new_val)

        assert "Parameter {} is read-only".format(test_param_accessor.callable_ro_path) \
            in str(excinfo.value)

    def test_callable_rw_accessor_get(self, test_param_accessor):
        """Test that a callable RW accessor returns the correct value."""
        assert test_param_accessor.callable_rw_accessor.get() == \
            test_param_accessor.callable_rw_value

    def test_callable_rw_accessor_set(self, test_param_accessor):
        """Test that a callable RW accessor set call sets the correct value."""
        old_val = test_param_accessor.callable_rw_value
        new_val = 'bar'
        test_param_accessor.callable_rw_accessor.set(new_val)
        assert test_param_accessor.callable_rw_accessor.get() == new_val

        test_param_accessor.callable_rw_accessor.set(old_val)

    def test_static_rw_accessor_default_metadata(self, test_param_accessor):
        """Test that a static RW accessor has the appropriate default metadata."""
        param = test_param_accessor.static_rw_accessor.get(with_metadata=True)
        assert(isinstance(param, dict))
        assert param['value'] == test_param_accessor.static_rw_value
        assert param['type'] == type(test_param_accessor.static_rw_value).__name__
        assert param['writeable'] == True

    def test_callable_ro_accessor_default_metadata(self, test_param_accessor):
        """Test that a callable RO accesor has the appropriate default metadata."""
        param = test_param_accessor.callable_ro_accessor.get(with_metadata=True)
        assert param['value'] == test_param_accessor.callable_ro_value
        assert param['type'] == type(test_param_accessor.callable_ro_value).__name__
        assert param['writeable'] == False

    def test_callable_rw_accessor_default_metadata(self, test_param_accessor):
        """Test that a callable RW accesor has the appropriate default metadata."""
        param = test_param_accessor.callable_rw_accessor.get(with_metadata=True)
        assert param['value'] == test_param_accessor.callable_rw_value
        assert param['type'] == type(test_param_accessor.callable_rw_value).__name__
        assert param['writeable'] == True

    def test_metadata_param_accessor_metadata(self, test_param_accessor):
        """Test that a parameter accessor has the correct metadata fields."""
        param = test_param_accessor.md_accessor.get(with_metadata=True)
        for md_field in test_param_accessor.md_param_metadata:
            assert md_field in param
            assert param[md_field] == test_param_accessor.md_param_metadata[md_field]
        assert param['value'] == test_param_accessor.md_param_val
        assert param['type'] == type(test_param_accessor.md_param_val).__name__
        assert param['writeable'] == True

    def test_param_accessor_bad_metadata_arg(self, test_param_accessor):
        """Test that a parameter accessor with a bad metadata argument raises an error."""
        bad_metadata_argument = 'foo'
        bad_metadata = {bad_metadata_argument: 'bar'}
        with pytest.raises(ParameterTreeError) as excinfo:
            _ = ParameterAccessor(
                test_param_accessor.static_rw_path + '/', 
                test_param_accessor.static_rw_value, **bad_metadata
            )

        assert "Invalid metadata argument: {}".format(bad_metadata_argument) \
            in str(excinfo.value)
        
    def test_param_accessor_set_type_mismatch(self, test_param_accessor):
        """
        Test that setting the value of a parameter accessor with the incorrected type raises
        an error.
        """
        bad_value = 1.234
        bad_value_type = type(bad_value).__name__
        
        with pytest.raises(ParameterTreeError) as excinfo:
            test_param_accessor.callable_rw_accessor.set(bad_value)

        assert "Type mismatch setting {}: got {} expected {}".format(
                test_param_accessor.callable_rw_path, bad_value_type, 
                type(test_param_accessor.callable_rw_value).__name__
            ) in str(excinfo.value)

    def test_param_accessor_bad_allowed_value(self, test_param_accessor):
        """
        Test the setting the value of a parameter accessor to a disallowed value raises an error.
        """
        bad_value = 222
        with pytest.raises(ParameterTreeError) as excinfo:
            test_param_accessor.md_accessor.set(bad_value)

        assert "{} is not an allowed value for {}".format(
                bad_value, test_param_accessor.md_param_path
            ) in str(excinfo.value)

    def test_param_accessor_value_below_min(self, test_param_accessor):
        """
        Test that setting the value of a parameter accessor below the minimum allowed raises an
        error.
        """
        bad_value = 1
        with pytest.raises(ParameterTreeError) as excinfo:
            test_param_accessor.md_minmax_accessor.set(bad_value)

        assert "{} is below the minimum value {} for {}".format(
                bad_value, test_param_accessor.md_minmax_metadata['min'], 
                test_param_accessor.md_minmax_path
            ) in str(excinfo.value)

    def test_param_accessor_value_above_max(self, test_param_accessor):
        """
        Test that setting the value of a parameter accessor above the maximum allowed raises an
        error.
        """
        bad_value = 100000
        with pytest.raises(ParameterTreeError) as excinfo:
            test_param_accessor.md_minmax_accessor.set(bad_value)

        assert "{} is above the maximum value {} for {}".format(
                bad_value, test_param_accessor.md_minmax_metadata['max'], 
                test_param_accessor.md_minmax_path
            ) in str(excinfo.value)

class ParameterTreeTestFixture(object):
    """Container class for use in fixtures testing ParameterTree."""

    def __init__(self):

        self.int_value = 1234
        self.float_value = 3.1415
        self.bool_value = True
        self.str_value = 'theString'
        self.list_values = list(range(4))

        self.simple_dict = {
            'intParam': self.int_value,
            'floatParam': self.float_value,
            'boolParam': self.bool_value,
            'strParam':  self.str_value,
        }

        self.accessor_params = {
            'one': 1,
            'two': 2,
            'pi': 3.14
        }
        self.simple_tree = ParameterTree(self.simple_dict)

        # Set up nested dict of parameters for a more complex tree
        self.nested_dict = self.simple_dict.copy()
        self.nested_dict['branch'] = {
            'branchIntParam': 4567,
            'branchStrParam': 'theBranch',
        }
        self.nested_tree = ParameterTree(self.nested_dict)

        self.callback_tree = deepcopy(self.nested_tree)
        self.callback_tree.add_callback('branch/', self.branch_callback)

        self.branch_callback_count = 0

        self.complex_tree_branch = ParameterTree(deepcopy(self.nested_dict))
        self.complex_tree_branch.add_callback('', self.branch_callback)

        self.complex_tree = ParameterTree({
            'intParam': self.int_value,
            'callableRoParam': (lambda: self.int_value, None),
            'callableAccessorParam': (self.get_accessor_param, None),
            'listParam': self.list_values,
            'branch': self.complex_tree_branch,
        })

        self.list_tree = ParameterTree({
            'main' : [
                self.simple_dict.copy(),
                list(self.list_values)
                ]
        })

        self.simple_list_tree = ParameterTree({
            'list_param': [10, 11, 12, 13]
        })

    def get_accessor_param(self):
        return self.accessor_params

    def branch_callback(self, path, value):
        self.branch_callback_count += 1
        # print("branch_callback call #{}: on path {} with value {}".format(
        #     self.branch_callback_count, path, value))

    def setup(self):
        TestParameterTree.branch_callback_count = 0
        pass


@pytest.fixture(scope="class")
def test_param_tree():
    """Test fixture for testing ParameterTree."""
    test_param_tree = ParameterTreeTestFixture()
    yield test_param_tree

class TestParameterTree():
    """Calss to test the behaviour of the ParameterTree object."""

    def test_simple_tree_returns_dict(self, test_param_tree):
        """Test the get on a simple tree returns a dict."""
        dt_vals = test_param_tree.simple_tree.get('')
        assert dt_vals, test_param_tree.simple_dict

    def test_simple_tree_single_values(self, test_param_tree):
        """Test that getting single values from a simple tree returns the correct values."""
        dt_int_val = test_param_tree.simple_tree.get('intParam')
        assert dt_int_val['intParam'] == test_param_tree.int_value

        dt_float_val = test_param_tree.simple_tree.get('floatParam')
        assert dt_float_val['floatParam'] == test_param_tree.float_value

        dt_bool_val = test_param_tree.simple_tree.get('boolParam')
        assert dt_bool_val['boolParam'] == test_param_tree.bool_value

        dt_str_val = test_param_tree.simple_tree.get('strParam')
        assert dt_str_val['strParam'] == test_param_tree.str_value

    def test_simple_tree_missing_value(self, test_param_tree):
        """Test that getting a missing value from a simple tree raises an error."""
        with pytest.raises(ParameterTreeError) as excinfo:
            test_param_tree.simple_tree.get('missing')

        assert 'Invalid path: missing' in str(excinfo.value)

    def test_nested_tree_returns_nested_dict(self, test_param_tree):
        """Test that getting a nested tree return a dict."""
        nested_dt_vals = test_param_tree.nested_tree.get('')
        assert nested_dt_vals == test_param_tree.nested_dict

    def test_nested_tree_branch_returns_dict(self, test_param_tree):
        """Test that getting a tree from within a nested tree returns a dict."""
        branch_vals = test_param_tree.nested_tree.get('branch')
        assert branch_vals['branch'] == test_param_tree.nested_dict['branch']

    def test_nested_tree_trailing_slash(self, test_param_tree):
        """Test that getting a tree with trailing slash returns the correct dict."""
        branch_vals = test_param_tree.nested_tree.get('branch/')
        assert branch_vals['branch'] == test_param_tree.nested_dict['branch']

    def test_callback_modifies_branch_value(self, test_param_tree):
        """Test that the modifying a branch below a callback does change the branch."""
        branch_data = deepcopy(test_param_tree.nested_dict['branch'])
        branch_data['branchIntParam'] = 90210

        test_param_tree.callback_tree.set('branch', branch_data)

        modified_branch_vals = test_param_tree.callback_tree.get('branch')
        assert modified_branch_vals['branch'] == branch_data
        assert test_param_tree.branch_callback_count == len(branch_data)

    def test_callback_modifies_single_branch_value(self, test_param_tree):
        """Test that modifying a single branch value below a callback works correctly."""
        int_param = 22603
        test_param_tree.callback_tree.set('branch/branchIntParam', int_param)

        val = test_param_tree.callback_tree.get('branch/branchIntParam')
        assert val['branchIntParam'] == int_param

    def test_callback_with_extra_branch_paths(self, test_param_tree):
        """
        Test that modifiying a branch in a callback tree with extra parameters raises an error.
        """
        branch_data = deepcopy(test_param_tree.nested_dict['branch'])
        branch_data['extraParam'] = 'oops'

        with pytest.raises(ParameterTreeError) as excinfo:
            test_param_tree.callback_tree.set('branch', branch_data)

        assert 'Invalid path' in str(excinfo.value)

    def test_complex_tree_calls_leaf_nodes(self, test_param_tree):
        """
        Test that accessing valyus in a complex tree returns the correct values for 
        static and callable parameters.
        """
        complex_vals = test_param_tree.complex_tree.get('')
        assert complex_vals['intParam'] == test_param_tree.int_value
        assert complex_vals['callableRoParam'] == test_param_tree.int_value

    def test_complex_tree_access_list_param(self, test_param_tree):
        """Test that getting a list parameter from a complex tree returns the appropriate values."""
        list_param_vals = test_param_tree.complex_tree.get('listParam')
        assert list_param_vals['listParam'] == test_param_tree.list_values

    def test_complex_tree_access_list_param_element(self, test_param_tree):
        """Test that getting single values from a list element returns the correct values"""
        for elem in test_param_tree.list_values:
            list_param_elem = test_param_tree.complex_tree.get('listParam/{}'.format(elem))
            assert list_param_elem['{}'.format(elem)] == elem

    def test_complex_tree_accessor(self, test_param_tree):
        """
        Test that getting a value from a complex tree with a callable accessor returns
        the correct value.
        """
        accessor_val = test_param_tree.complex_tree.get('callableAccessorParam/one')
        assert accessor_val['one']==  test_param_tree.accessor_params['one']

    def test_complex_tree_callable_readonly(self, test_param_tree):
        """
        Test that attempting to set the value of a RO callable parameter in a tree raises an
        error.
        """
        with pytest.raises(ParameterTreeError) as excinfo:
            test_param_tree.complex_tree.set('callableRoParam', 1234)

        assert 'Parameter callableRoParam is read-only' in str(excinfo.value)

    def test_complex_tree_set_invalid_path(self, test_param_tree):
        """
        Test that attempting to set the value of an element in a complex tree on a path
        that does not exist raises an error.
        """
        invalid_path = 'invalidPath/toNothing'

        with pytest.raises(ParameterTreeError) as excinfo:
            test_param_tree.complex_tree.set(invalid_path, 0)

        assert 'Invalid path: {}'.format(invalid_path) in str(excinfo.value)

    def test_complex_tree_set_top_level(self, test_param_tree):
        """Test that setting the top level of a complex tree correctly sets all values."""
        complex_vals = test_param_tree.complex_tree.get('')
        complex_vals_copy = deepcopy(complex_vals)
        del complex_vals_copy['callableRoParam']
        del complex_vals_copy['callableAccessorParam']

        test_param_tree.complex_tree.set('', complex_vals_copy)
        complex_vals2 = test_param_tree.complex_tree.get('')
        assert complex_vals == complex_vals2

    def test_complex_tree_inject_spurious_dict(self, test_param_tree):
        """
        Test that attempting to attempt a dictionary into the position of a non-dict parameter
        raises in error.
        """
        param_data = {'intParam': 9876}

        with pytest.raises(ParameterTreeError) as excinfo:
            test_param_tree.complex_tree.set('intParam', param_data)

        assert 'Type mismatch updating intParam' in str(excinfo.value)

    def test_list_tree_get_indexed(self, test_param_tree):
        """
        Test that it is possible to get a value by index from a list parameter.
        """
        ret = test_param_tree.list_tree.get("main/1")
        assert ret == {'1':test_param_tree.list_values}

    def test_list_tree_set_indexed(self, test_param_tree):
        """
        Test that it is possible to set a value by index on a list parameter.
        """
        test_param_tree.list_tree.set("main/1/2", 7)
        assert test_param_tree.list_tree.get("main/1/2") == {'2': 7}

    def test_list_tree_set_from_root(self, test_param_tree):
        """Test that it is possible to set a list tree from its root."""
        tree_data = {
    	    'main' : [
                {
                    'intParam': 0,
                    'floatParam': 0.00,
                    'boolParam': False,
                    'strParam':  "test",
                },
		        [1,2,3,4]
            ]
	    }

        test_param_tree.list_tree.set("",tree_data)
        assert test_param_tree.list_tree.get("main") == tree_data

    def test_list_tree_from_dict(self, test_param_tree):
        """TEet that a list tree can be set with a dict of index/values."""
        new_list_param = {0: 0, 1: 1, 2: 2, 3: 3}
        test_param_tree.simple_list_tree.set('list_param', new_list_param)
        assert  test_param_tree.simple_list_tree.get(
            'list_param')['list_param']== list(new_list_param.values())
            

    def test_list_tree_from_dict_bad_index(self, test_param_tree):
        """
        Test that setting a list tree from a dict with an index outside the current range
        raises an error.
        """
        new_list_param = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5}
        with pytest.raises(ParameterTreeError) as excinfo:
            test_param_tree.simple_list_tree.set('list_param', new_list_param)

        assert "Invalid path: list_param/4 list index out of range" in str(excinfo.value)

    def test_bad_tuple_node_raises_error(self, test_param_tree):
        """Test that constructing a parameter tree with an immutable tuple raises an error."""
        bad_node = 'bad'
        bad_data = tuple(range(4))
        bad_tree = {
            bad_node: bad_data
        }
        with pytest.raises(ParameterTreeError) as excinfo:
            tree = ParameterTree(bad_tree)

        assert "not a valid leaf node" in str(excinfo.value)


class RwParameterTreeTestFixture(object):
    """Container class for use in read-write parameter tree  test fixtures."""
    def __init__(self):

        self.int_rw_param = 4576
        self.int_ro_param = 255374
        self.int_rw_value = 9876
        self.int_wo_param = 0

        self.rw_value_set_called = False

        self.nested_rw_param = 53.752
        self.nested_ro_value = 9.8765

        nested_tree = ParameterTree({
            'nestedRwParam': (self.nestedRwParamGet, self.nestedRwParamSet),
            'nestedRoParam': self.nested_ro_value
        })

        self.rw_callable_tree = ParameterTree({
            'intCallableRwParam': (self.intCallableRwParamGet, self.intCallableRwParamSet),
            'intCallableRoParam': (self.intCallableRoParamGet, None),
            'intCallableWoParam': (None, self.intCallableWoParamSet),
            'intCallableRwValue': (self.int_rw_value, self.intCallableRwValueSet),
            'branch': nested_tree
        })

    def intCallableRwParamSet(self, value):
        self.int_rw_param = value

    def intCallableRwParamGet(self):
        return self.int_rw_param

    def intCallableRoParamGet(self):
        return self.int_ro_param

    def intCallableWoParamSet(self, value):
        self.int_wo_param = value

    def intCallableRwValueSet(self, value):
        self.rw_value_set_called = True

    def nestedRwParamSet(self, value):
        self.nested_rw_param = value

    def nestedRwParamGet(self):
        return self.nested_rw_param


@pytest.fixture(scope="class")
def test_rw_tree():
    """Test fixture for use in testing read-write parameter trees."""
    test_rw_tree = RwParameterTreeTestFixture()
    yield test_rw_tree

class TestRwParameterTree():
    """Class to test behaviour of read-write parameter trees."""

    def test_rw_tree_simple_get_values(self, test_rw_tree):
        """Test getting simple values from a RW tree returns the correct values."""
        dt_rw_int_param = test_rw_tree.rw_callable_tree.get('intCallableRwParam')
        assert dt_rw_int_param['intCallableRwParam'] == test_rw_tree.int_rw_param

        dt_ro_int_param = test_rw_tree.rw_callable_tree.get('intCallableRoParam')
        assert dt_ro_int_param['intCallableRoParam'] == test_rw_tree.int_ro_param

        dt_rw_int_value = test_rw_tree.rw_callable_tree.get('intCallableRwValue')
        assert dt_rw_int_value['intCallableRwValue'] == test_rw_tree.int_rw_value

    def test_rw_tree_simple_set_value(self, test_rw_tree):
        """Test that setting a value in a RW tree updates and returns the correct value."""
        new_int_value = 91210
        test_rw_tree.rw_callable_tree.set('intCallableRwParam', new_int_value)

        dt_rw_int_param = test_rw_tree.rw_callable_tree.get('intCallableRwParam')
        assert dt_rw_int_param['intCallableRwParam'] == new_int_value

    def test_rw_tree_set_ro_param(self, test_rw_tree):
        """Test that attempting to set a RO parameter raises an error."""
        with pytest.raises(ParameterTreeError) as excinfo:
            test_rw_tree.rw_callable_tree.set('intCallableRoParam', 0)

        assert 'Parameter intCallableRoParam is read-only' in str(excinfo.value)

    def test_rw_callable_tree_set_wo_param(self, test_rw_tree):
        """Test that setting a write-only parameter (!!) sets the correct value."""
        new_value = 1234
        test_rw_tree.rw_callable_tree.set('intCallableWoParam', new_value)
        assert test_rw_tree.int_wo_param == new_value

    def test_rw_callable_tree_set_rw_value(self, test_rw_tree):
        """Test that setting a callable RW value calls the appropriate set method."""
        new_value = 1234
        test_rw_tree.rw_callable_tree.set('intCallableRwValue', new_value)
        assert test_rw_tree.rw_value_set_called

    def test_rw_callable_nested_param_get(self, test_rw_tree):
        """Test the getting a nested callable RW parameter returns the correct value."""
        dt_nested_param = test_rw_tree.rw_callable_tree.get('branch/nestedRwParam')
        assert dt_nested_param['nestedRwParam'] == test_rw_tree.nested_rw_param

    def test_rw_callable_nested_param_set(self, test_rw_tree):
        """Test that setting a nested callable RW parameter sets the correct value."""
        new_float_value = test_rw_tree.nested_rw_param + 2.3456
        test_rw_tree.rw_callable_tree.set('branch/nestedRwParam', new_float_value)
        assert test_rw_tree.nested_rw_param == new_float_value

    def test_rw_callable_nested_tree_set(self, test_rw_tree):
        """Test the setting a value within a callable nested tree updated the value correctly."""
        nested_branch = test_rw_tree.rw_callable_tree.get('branch')['branch']
        new_rw_param_val = 45.876
        nested_branch['nestedRwParam'] = new_rw_param_val
        test_rw_tree.rw_callable_tree.set('branch', nested_branch)
        new_branch = test_rw_tree.rw_callable_tree.get('branch')['branch']
        assert new_branch['nestedRwParam'], new_rw_param_val

    def test_rw_callable_nested_tree_set_trailing_slash(self, test_rw_tree):
        """
        Test that setting a callable nested tree with a trailing slash in the path
        sets the value correctly.
        """
        nested_branch = test_rw_tree.rw_callable_tree.get('branch/')['branch']
        new_rw_param_val = 24.601
        nested_branch['nestedRwParam'] = new_rw_param_val
        test_rw_tree.rw_callable_tree.set('branch/', nested_branch)
        new_branch = test_rw_tree.rw_callable_tree.get('branch/')['branch']
        assert new_branch['nestedRwParam'] == new_rw_param_val


class ParameterTreeMetadataTestFixture():
    """Container class for use in test fixtures testing parameter tree metadata."""

    def __init__(self):

        self.int_rw_param = 100
        self.float_ro_param = 4.6593
        self.int_ro_param = 1000
        self.int_enum_param = 0
        self.int_enum_param_allowed_values = [0, 1, 2, 3, 5, 8, 13]

        self.int_rw_param_metadata = {
            "min": 0,
            "max": 1000,
            "units": "arbitrary",
            "name": "intCallableRwParam",
            "description": "A callable integer RW parameter"
        }

        self.metadata_tree_dict = {
            'name': 'Metadata Tree',
            'description': 'A paramter tree to test metadata',
            'floatRoParam': (self.floatRoParamGet,),
            'intRoParam': (self.intRoParamGet, {"units": "seconds"}),
            'intCallableRwParam': (
                self.intCallableRwParamGet, self.intCallableRwParamSet, self.int_rw_param_metadata
            ),
            'intEnumParam': (0, {"allowed_values": self.int_enum_param_allowed_values}),
            'valueParam': (24601,)
        }
        self.metadata_tree = ParameterTree(self.metadata_tree_dict)

    def intCallableRwParamSet(self, value):
        self.int_rw_param = value

    def intCallableRwParamGet(self):
        return self.int_rw_param

    def floatRoParamGet(self):
        return self.float_ro_param
    
    def intRoParamGet(self):
        return self.int_ro_param


@pytest.fixture(scope="class")
def test_tree_metadata():
    """Test fixture for use in testing parameter tree metadata."""
    test_tree_metadata = ParameterTreeMetadataTestFixture()
    yield test_tree_metadata

class TestParameterTreeMetadata():

    def test_callable_rw_param_metadata(self, test_tree_metadata):
        """Test that a getting RW parameter with metadata returns the appropriate metadata."""
        int_param_with_metadata = test_tree_metadata.metadata_tree.get(
            "intCallableRwParam",with_metadata=True)
        int_param = test_tree_metadata.metadata_tree.get("intCallableRwParam")["intCallableRwParam"]

        expected_metadata = test_tree_metadata.int_rw_param_metadata
        expected_metadata["value"] = int_param
        expected_metadata["type"] = 'int'
        expected_metadata["writeable"] = True
        expected_param = {"intCallableRwParam" : expected_metadata}
        
        assert int_param_with_metadata == expected_param

    def test_get_filters_tree_metadata(self, test_tree_metadata):
        """
        Test that attempting to get a metadata field for a parameter as if it was path itself
        raises an error.
        """
        metadata_path = "name"
        with pytest.raises(ParameterTreeError) as excinfo:
            test_tree_metadata.metadata_tree.get(metadata_path)

        assert "Invalid path: {}".format(metadata_path) in str(excinfo.value)

    def test_set_tree_rejects_metadata(self, test_tree_metadata):
        """
        Test that attampeting to set a metadata field as if it was a parameter raises an error.
        """
        metadata_path = "name"
        with pytest.raises(ParameterTreeError) as excinfo:
            test_tree_metadata.metadata_tree.set(metadata_path, "invalid")

        assert "Invalid path: {}".format(metadata_path) in str(excinfo.value)

    def test_enum_param_allowed_values(self, test_tree_metadata):
        """Test that setting an enumerated parameter with an allowed value succeeds."""
        for value in test_tree_metadata.int_enum_param_allowed_values:
            test_tree_metadata.metadata_tree.set("intEnumParam", value)
            set_value = test_tree_metadata.metadata_tree.get("intEnumParam")["intEnumParam"]
            assert value == set_value
    
    def test_enum_param_bad_value(self, test_tree_metadata):
        """
        Test that attempting to set a disallowed value for an enumerated parameter raises an error.
        """
        bad_value = test_tree_metadata.int_enum_param_allowed_values[-1] + 1
        with pytest.raises(ParameterTreeError) as excinfo:
            test_tree_metadata.metadata_tree.set("intEnumParam", bad_value)

        assert "{} is not an allowed value".format(bad_value) in str(excinfo.value)

    def test_ro_param_has_writeable_metadata_field(self, test_tree_metadata):
        """Test that a RO parameter has the writeable metadata field set to false."""
        ro_param = test_tree_metadata.metadata_tree.get("floatRoParam", with_metadata=True)
        assert ro_param["floatRoParam"]["writeable"] == False

    def test_ro_param_not_writeable(self, test_tree_metadata):
        """Test that attempting to write to a RO parameter with metadata raises an error."""
        with pytest.raises(ParameterTreeError) as excinfo:
            test_tree_metadata.metadata_tree.set("floatRoParam", 3.141275)
        assert "Parameter {} is read-only".format("floatRoParam") in str(excinfo.value)

    def test_value_param_writeable(self, test_tree_metadata):
        """Test that a value parameter is writeable and has the correct metadata flag."""
        new_value = 90210
        test_tree_metadata.metadata_tree.set("valueParam", new_value)
        set_param = test_tree_metadata.metadata_tree.get(
            "valueParam", with_metadata=True)["valueParam"]
        assert set_param["value"] == new_value
        assert set_param["writeable"] == True

    def test_rw_param_below_min_value(self, test_tree_metadata):
        """
        Test that attempting to set a value for a RW parameter below the specified minimum
        raises an error.
        """
        low_value = -1
        with pytest.raises(ParameterTreeError) as excinfo:
            test_tree_metadata.metadata_tree.set("intCallableRwParam", low_value)

        assert "{} is below the minimum value {} for {}".format(
                low_value, test_tree_metadata.int_rw_param_metadata["min"], 
                "intCallableRwParam") in str(excinfo.value)
        

    def test_rw_param_above_max_value(self, test_tree_metadata):
        """
        Test that attempting to set a value for a RW parameter above the specified maximum
        raises an error.
        """
        high_value = 100000
        with pytest.raises(ParameterTreeError) as excinfo:
            test_tree_metadata.metadata_tree.set("intCallableRwParam", high_value)

        assert "{} is above the maximum value {} for {}".format(
                high_value, test_tree_metadata.int_rw_param_metadata["max"], 
                "intCallableRwParam") in str(excinfo.value)
