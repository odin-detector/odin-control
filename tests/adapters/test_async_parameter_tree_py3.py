"""Test the AsyncParameterTree classes.

This module implements unit test cases for the AsyncParameterAccessor and AsyncParameterTree
classes.

Tim Nicholls, STFC Detector Systems Software Group.
"""

import asyncio
import math
import sys

from copy import deepcopy

import pytest

if sys.version_info[0] < 3:
    pytest.skip("Skipping async tests", allow_module_level=True)
else:

    from  odin.adapters.async_parameter_tree import (
        AsyncParameterAccessor,AsyncParameterTree, ParameterTreeError
    )
    import pytest_asyncio
    try:
        asyncio_fixture_decorator = pytest_asyncio.fixture
    except AttributeError:
        asyncio_fixture_decorator = pytest.fixture


class AwaitableTestFixture(object):
    """Class implementing an awaitable test fixture."""
    def __init__(self, awaitable_cls=None):
        self.awaitable_cls = awaitable_cls

    def __await__(self):

        async def closure():
            awaitables = [attr for attr in self.__dict__.values() if isinstance(
                attr,  self.awaitable_cls
            )]
            await asyncio.gather(*awaitables)
            return self
        
        return closure().__await__()  
        
class AsyncParameterAccessorTestFixture(AwaitableTestFixture):
    """Test fixture of AsyncParameterAccessor test cases."""
    def __init__(self):

        super(AsyncParameterAccessorTestFixture, self).__init__(AsyncParameterAccessor)

        self.static_rw_path = 'static_rw'
        self.static_rw_value = 2.76923
        self.static_rw_accessor = AsyncParameterAccessor(
            self.static_rw_path + '/', self.static_rw_value
        )

        self.sync_ro_value = 1234
        self.sync_ro_path = 'sync_ro'
        self.sync_ro_accessor = AsyncParameterAccessor(
            self.sync_ro_path + '/', self.sync_ro_get
        )

        self.sync_rw_value = 'foo'
        self.sync_rw_path = 'sync_rw'
        self.sync_rw_accessor = AsyncParameterAccessor(
            self.sync_rw_path + '/', self.sync_rw_get, self.sync_rw_set
        )

        self.async_ro_value = 5593
        self.async_ro_path = 'async_ro'
        self.async_ro_accessor = AsyncParameterAccessor(
            self.async_ro_path + '/', self.async_ro_get
        )

        self.async_rw_value = math.pi
        self.async_rw_path = 'async_rw'
        self.async_rw_accessor = AsyncParameterAccessor(
            self.async_rw_path + '/', self.async_rw_get, self.async_rw_set
        )

        self.md_param_path ='mdparam'
        self.md_param_value = 456
        self.md_param_metadata = {
            'min' : 100,
            'max' : 1000,
            "allowed_values": [100, 123, 456, 789, 1000],
            "name": "Test Parameter",
            "description": "This is a test parameter",
            "units": "furlongs/fortnight",
            "display_precision": 0,
        }
        self.md_accessor = AsyncParameterAccessor(
            self.md_param_path + '/', self.async_md_get, self.async_md_set, **self.md_param_metadata
        )

        self.md_minmax_path = 'minmaxparam'
        self.md_minmax_value = 500
        self.md_minmax_metadata = {
            'min': 100,
            'max': 1000
        }
        self.md_minmax_accessor = AsyncParameterAccessor(
            self.md_minmax_path + '/', self.async_md_minmax_get, self.async_md_minmax_set,
            **self.md_minmax_metadata
        )

    def sync_ro_get(self):
        return self.sync_ro_value

    def sync_rw_get(self):
        return self.sync_rw_value

    def sync_rw_set(self, value):
        self.sync_rw_value = value

    async def async_ro_get(self):
        await asyncio.sleep(0)
        return self.async_ro_value

    async def async_rw_get(self):
        await asyncio.sleep(0)
        return self.async_rw_value

    async def async_rw_set(self, value):
        await asyncio.sleep(0)
        self.async_rw_value = value

    async def async_md_get(self):
        await asyncio.sleep(0)
        return self.md_param_value

    async def async_md_set(self, value):
        await asyncio.sleep(0)
        self.async_md_param_value = value

    async def async_md_minmax_get(self):
        await asyncio.sleep(0)
        return self.md_minmax_value

    async def async_md_minmax_set(self, value):
        await asyncio.sleep(0)
        self.md_minmax_value = value

@pytest.fixture(scope="class")
def event_loop():
    """Redefine the pytest.asyncio event loop fixture to have class scope."""
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

@asyncio_fixture_decorator(scope="class")
async def test_param_accessor():
    """Test fixture used in testing ParameterAccessor behaviour."""
    test_param_accessor = await AsyncParameterAccessorTestFixture()
    yield test_param_accessor

@pytest.mark.asyncio
class TestAsyncParameterAccessor():
    """Class to test AsyncParameterAccessor behaviour"""

    async def test_static_rw_accessor_get(self, test_param_accessor):
        """Test that a static RW accessor get call returns the correct value."""
        value = await test_param_accessor.static_rw_accessor.get() 
        assert value == test_param_accessor.static_rw_value

    async def test_static_rw_accessor_set(self, test_param_accessor):
        """Test that a static RW accessor set call sets the correct value."""
        old_val = test_param_accessor.static_rw_value
        new_val = 1.234
        await test_param_accessor.static_rw_accessor.set(new_val)
        value = await test_param_accessor.static_rw_accessor.get() 
        assert value == new_val

        await test_param_accessor.static_rw_accessor.set(old_val)

    async def test_sync_ro_accessor_get(self, test_param_accessor):
        """Test that a synchronous callable RO accessor get call returns the correct value."""
        value = await test_param_accessor.sync_ro_accessor.get()
        assert value == test_param_accessor.sync_ro_value

    async def test_sync_ro_accessor_set(self, test_param_accessor):
        """Test that a synchronous callable RO accessor set call raises an error."""
        new_val = 91265
        with pytest.raises(ParameterTreeError) as excinfo:
            await test_param_accessor.sync_ro_accessor.set(new_val)

        assert "Parameter {} is read-only".format(test_param_accessor.sync_ro_path) \
            in str(excinfo.value)

    async def test_sync_rw_accessor_get(self, test_param_accessor):
        """Test that a synchronous callable RW accessor returns the correct value."""
        value = await test_param_accessor.sync_rw_accessor.get()
        assert value == test_param_accessor.sync_rw_value

    async def test_sync_rw_accessor_set(self, test_param_accessor):
        """Test that a synchronous callable RW accessor set call sets the correct value."""
        old_val = test_param_accessor.sync_rw_value
        new_val = 'bar'
        await test_param_accessor.sync_rw_accessor.set(new_val)
        value = await test_param_accessor.sync_rw_accessor.get()
        assert value == new_val

        await test_param_accessor.sync_rw_accessor.set(old_val)

    async def test_async_ro_accessor_get(self, test_param_accessor):
        """Test that an asynchronous callable RO accessor get call returns the correct value."""
        value = await test_param_accessor.async_ro_accessor.get()
        assert value == test_param_accessor.async_ro_value

    async def test_async_ro_accessor_set(self, test_param_accessor):
        """Test that an asynchronous callable RO accessor set call raises an error."""
        new_val = 91265
        with pytest.raises(ParameterTreeError) as excinfo:
            await test_param_accessor.async_ro_accessor.set(new_val)

        assert "Parameter {} is read-only".format(test_param_accessor.async_ro_path) \
            in str(excinfo.value)

    async def test_async_rw_accessor_get(self, test_param_accessor):
        """Test that an asynchronous callable RW accessor get returns the correct value."""
        value = await test_param_accessor.async_rw_accessor.get()
        assert value == test_param_accessor.async_rw_value

    async def test_async_rw_accessor_set(self, test_param_accessor):
        """Test that an asynchronous callable RW accessor sets the correct value."""
        old_val = test_param_accessor.async_rw_value
        new_val = old_val * 2
        await test_param_accessor.async_rw_accessor.set(new_val)
        value = await test_param_accessor.async_rw_accessor.get()
        assert value == new_val

    async def test_static_rw_accessor_default_metadata(self, test_param_accessor):
        """Test that a static RW accessor has the appropriate default metadata."""
        param = await test_param_accessor.static_rw_accessor.get(with_metadata=True)
        assert(isinstance(param, dict))
        assert param['value'] == test_param_accessor.static_rw_value
        assert param['type'] == type(test_param_accessor.static_rw_value).__name__
        assert param['writeable'] == True

    async def test_sync_ro_accessor_default_metadata(self, test_param_accessor):
        """Test that a synchronous callable RO accesor has the appropriate default metadata."""
        param = await test_param_accessor.sync_ro_accessor.get(with_metadata=True)
        assert param['value'] == test_param_accessor.sync_ro_value
        assert param['type'] == type(test_param_accessor.sync_ro_value).__name__
        assert param['writeable'] == False

    async def test_sync_rw_accessor_default_metadata(self, test_param_accessor):
        """Test that a synchronous callable RW accesor has the appropriate default metadata."""
        param = await test_param_accessor.sync_rw_accessor.get(with_metadata=True)
        assert param['value'] == test_param_accessor.sync_rw_value
        assert param['type'] == type(test_param_accessor.sync_rw_value).__name__
        assert param['writeable'] == True

    async def test_sync_ro_accessor_default_metadata(self, test_param_accessor):
        """Test that a synchronous callable RO accesor has the appropriate default metadata."""
        param = await test_param_accessor.sync_ro_accessor.get(with_metadata=True)
        assert param['value'] == test_param_accessor.sync_ro_value
        assert param['type'] == type(test_param_accessor.sync_ro_value).__name__
        assert param['writeable'] == False

    async def test_async_rw_accessor_default_metadata(self, test_param_accessor):
        """Test that an asynchronous callable RW accesor has the appropriate default metadata."""
        param = await test_param_accessor.async_rw_accessor.get(with_metadata=True)
        assert param['value'] == test_param_accessor.async_rw_value
        assert param['type'] == type(test_param_accessor.async_rw_value).__name__
        assert param['writeable'] == True

    async def test_async_ro_accessor_default_metadata(self, test_param_accessor):
        """Test that an asynchronous callable RO accesor has the appropriate default metadata."""
        param = await test_param_accessor.async_ro_accessor.get(with_metadata=True)
        assert param['value'] == test_param_accessor.async_ro_value
        assert param['type'] == type(test_param_accessor.async_ro_value).__name__
        assert param['writeable'] == False

    async def test_metadata_param_accessor_metadata(self, test_param_accessor):
        """Test that a parameter accessor has the correct metadata fields."""
        param = await test_param_accessor.md_accessor.get(with_metadata=True)
        for md_field in test_param_accessor.md_param_metadata:
            assert md_field in param
            assert param[md_field] == test_param_accessor.md_param_metadata[md_field]
        assert param['value'] == test_param_accessor.md_param_value
        assert param['type'] == type(test_param_accessor.md_param_value).__name__
        assert param['writeable'] == True

    async def test_param_accessor_bad_metadata_arg(self, test_param_accessor):
        """Test that a parameter accessor with a bad metadata argument raises an error."""
        bad_metadata_argument = 'foo'
        bad_metadata = {bad_metadata_argument: 'bar'}
        with pytest.raises(ParameterTreeError) as excinfo:
            _ = await AsyncParameterAccessor(
                test_param_accessor.static_rw_path + '/', 
                test_param_accessor.static_rw_value, **bad_metadata
            )

        assert "Invalid metadata argument: {}".format(bad_metadata_argument) \
            in str(excinfo.value)

    async def test_param_accessor_set_type_mismatch(self, test_param_accessor):
        """
        Test that setting the value of a parameter accessor with the incorrected type raises
        an error.
        """
        bad_value = 'bar'
        bad_value_type = type(bad_value).__name__
        
        with pytest.raises(ParameterTreeError) as excinfo:
            await test_param_accessor.async_rw_accessor.set(bad_value)

        assert "Type mismatch setting {}: got {} expected {}".format(
                test_param_accessor.async_rw_path, bad_value_type, 
                type(test_param_accessor.async_rw_value).__name__
            ) in str(excinfo.value)

    async def test_param_accessor_bad_allowed_value(self, test_param_accessor):
        """
        Test the setting the value of a parameter accessor to a disallowed value raises an error.
        """
        bad_value = 222
        with pytest.raises(ParameterTreeError) as excinfo:
            await test_param_accessor.md_accessor.set(bad_value)

        assert "{} is not an allowed value for {}".format(
                bad_value, test_param_accessor.md_param_path
            ) in str(excinfo.value)

    async def test_param_accessor_value_below_min(self, test_param_accessor):
        """
        Test that setting the value of a parameter accessor below the minimum allowed raises an
        error.
        """
        bad_value = 1
        with pytest.raises(ParameterTreeError) as excinfo:
            await test_param_accessor.md_minmax_accessor.set(bad_value)

        assert "{} is below the minimum value {} for {}".format(
                bad_value, test_param_accessor.md_minmax_metadata['min'], 
                test_param_accessor.md_minmax_path
            ) in str(excinfo.value)

    async def test_param_accessor_value_above_max(self, test_param_accessor):
        """
        Test that setting the value of a parameter accessor above the maximum allowed raises an
        error.
        """
        bad_value = 100000
        with pytest.raises(ParameterTreeError) as excinfo:
            await test_param_accessor.md_minmax_accessor.set(bad_value)

        assert "{} is above the maximum value {} for {}".format(
                bad_value, test_param_accessor.md_minmax_metadata['max'], 
                test_param_accessor.md_minmax_path
            ) in str(excinfo.value)
        
        
class AsyncParameterTreeTestFixture(AwaitableTestFixture):
    """Container class for use in fixtures testing AsyncParameterTree."""

    def __init__(self):

        super(AsyncParameterTreeTestFixture, self).__init__(AsyncParameterTree)

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
        self.simple_tree = AsyncParameterTree(self.simple_dict)

        # Set up nested dict of parameters for a more complex tree
        self.nested_dict = self.simple_dict.copy()
        self.nested_dict['branch'] = {
            'branchIntParam': 4567,
            'branchStrParam': 'theBranch',
        }
        self.nested_tree = AsyncParameterTree(self.nested_dict)

        self.complex_tree = AsyncParameterTree({
            'intParam': self.int_value,
            'callableRoParam': (lambda: self.int_value, None),
            'callableAccessorParam': (self.get_accessor_param, None),
            'listParam': self.list_values,
            'branch': AsyncParameterTree(deepcopy(self.nested_dict)),
        })
       
        self.list_tree = AsyncParameterTree({
            'main' : [
                self.simple_dict.copy(),
                list(self.list_values)
                ]
        })

        self.simple_list_tree = AsyncParameterTree({
            'list_param': [10, 11, 12, 13]
        })

    async def async_ro_get(self):
        await asyncio.sleep(0)
        return self.async_ro_value

    async def nested_async_ro_get(self):
        await asyncio.sleep(0)
        return self.nested_async_ro_value

    async def get_accessor_param(self):
        await asyncio.sleep(0)
        return self.accessor_params


@asyncio_fixture_decorator(scope="class")
async def test_param_tree():
    """Test fixture used in testing AsyncParameterTree behaviour."""
    test_param_accessor = await AsyncParameterTreeTestFixture()
    yield test_param_accessor


@pytest.mark.asyncio
class TestAsyncParameterTree():

    async def test_simple_tree_returns_dict(self, test_param_tree):
        """Test the get on a simple tree returns a dict."""
        dt_vals = await test_param_tree.simple_tree.get('')
        assert dt_vals, test_param_tree.simple_dict
        assert True

    async def test_simple_tree_single_values(self, test_param_tree):
        """Test that getting single values from a simple tree returns the correct values."""
        dt_int_val = await test_param_tree.simple_tree.get('intParam')
        assert dt_int_val['intParam'] == test_param_tree.int_value

        dt_float_val = await test_param_tree.simple_tree.get('floatParam')
        assert dt_float_val['floatParam'] == test_param_tree.float_value

        dt_bool_val = await test_param_tree.simple_tree.get('boolParam')
        assert dt_bool_val['boolParam'] == test_param_tree.bool_value

        dt_str_val = await test_param_tree.simple_tree.get('strParam')
        assert dt_str_val['strParam'] == test_param_tree.str_value

    async def test_simple_tree_missing_value(self, test_param_tree):
        """Test that getting a missing value from a simple tree raises an error."""
        with pytest.raises(ParameterTreeError) as excinfo:
            await test_param_tree.simple_tree.get('missing')

        assert 'Invalid path: missing' in str(excinfo.value)

    async def test_nested_tree_returns_nested_dict(self, test_param_tree):
        """Test that getting a nested tree return a dict."""
        nested_dt_vals = await test_param_tree.nested_tree.get('')
        assert nested_dt_vals == test_param_tree.nested_dict

    async def test_nested_tree_branch_returns_dict(self, test_param_tree):
        """Test that getting a tree from within a nested tree returns a dict."""
        branch_vals = await test_param_tree.nested_tree.get('branch')
        assert branch_vals['branch'] == test_param_tree.nested_dict['branch']

    async def test_nested_tree_trailing_slash(self, test_param_tree):
        """Test that getting a tree with trailing slash returns the correct dict."""
        branch_vals = await test_param_tree.nested_tree.get('branch/')
        assert branch_vals['branch'] == test_param_tree.nested_dict['branch']

    async def test_set_with_extra_branch_paths(self, test_param_tree):
        """
        Test that modifiying a branch in a tree with extra parameters raises an error.
        """
        branch_data = deepcopy(test_param_tree.nested_dict['branch'])
        branch_data['extraParam'] = 'oops'

        with pytest.raises(ParameterTreeError) as excinfo:
            await test_param_tree.complex_tree.set('branch', branch_data)

        assert 'Invalid path' in str(excinfo.value)

    async def test_complex_tree_calls_leaf_nodes(self, test_param_tree):
        """
        Test that accessing valyus in a complex tree returns the correct values for 
        static and callable parameters.
        """
        complex_vals = await test_param_tree.complex_tree.get('')
        assert complex_vals['intParam'] == test_param_tree.int_value
        assert complex_vals['callableRoParam'] == test_param_tree.int_value

    async def test_complex_tree_access_list_param(self, test_param_tree):
        """Test that getting a list parameter from a complex tree returns the appropriate values."""
        list_param_vals = await test_param_tree.complex_tree.get('listParam')
        assert list_param_vals['listParam'] == test_param_tree.list_values
    
    async def test_complex_tree_callable_readonly(self, test_param_tree):
        """
        Test that attempting to set the value of a RO callable parameter in a tree raises an
        error.
        """
        with pytest.raises(ParameterTreeError) as excinfo:
            await test_param_tree.complex_tree.set('callableRoParam', 1234)

        assert 'Parameter callableRoParam is read-only' in str(excinfo.value)

    async def test_complex_tree_set_invalid_path(self, test_param_tree):
        """
        Test that attempting to set the value of an element in a complex tree on a path
        that does not exist raises an error.
        """
        invalid_path = 'invalidPath/toNothing'

        with pytest.raises(ParameterTreeError) as excinfo:
            await test_param_tree.complex_tree.set(invalid_path, 0)

        assert 'Invalid path: {}'.format(invalid_path) in str(excinfo.value)

    async def test_complex_tree_set_top_level(self, test_param_tree):
        """Test that setting the top level of a complex tree correctly sets all values."""
        complex_vals = await test_param_tree.complex_tree.get('')
        complex_vals_copy = deepcopy(complex_vals)
        del complex_vals_copy['callableRoParam']
        del complex_vals_copy['callableAccessorParam']

        await test_param_tree.complex_tree.set('', complex_vals_copy)
        complex_vals2 = await test_param_tree.complex_tree.get('')
        assert complex_vals == complex_vals2

    async def test_complex_tree_inject_spurious_dict(self, test_param_tree):
        """
        Test that attempting to attempt a dictionary into the position of a non-dict parameter
        raises in error.
        """
        param_data = {'intParam': 9876}

        with pytest.raises(ParameterTreeError) as excinfo:
            await test_param_tree.complex_tree.set('intParam', param_data)

        assert 'Type mismatch updating intParam' in str(excinfo.value)

    async def test_list_tree_get_indexed(self, test_param_tree):
        """
        Test that it is possible to get a value by index from a list parameter.
        """
        ret = await test_param_tree.list_tree.get("main/1")
        assert ret == {'1':test_param_tree.list_values}

    async def test_list_tree_set_indexed(self, test_param_tree):
        """
        Test that it is possible to set a value by index on a list parameter.
        """
        await test_param_tree.list_tree.set("main/1/2", 7)
        assert await test_param_tree.list_tree.get("main/1/2") == {'2': 7}

    async def test_list_tree_set_from_root(self, test_param_tree):
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

        await test_param_tree.list_tree.set("",tree_data)
        assert await test_param_tree.list_tree.get("main") == tree_data

    async def test_list_tree_from_dict(self, test_param_tree):
        """TEet that a list tree can be set with a dict of index/values."""
        new_list_param = {0: 0, 1: 1, 2: 2, 3: 3}
        await test_param_tree.simple_list_tree.set('list_param', new_list_param)
        result = await test_param_tree.simple_list_tree.get('list_param')
        assert result['list_param']== list(new_list_param.values())
            

    async def test_list_tree_from_dict_bad_index(self, test_param_tree):
        """
        Test that setting a list tree from a dict with an index outside the current range
        raises an error.
        """
        new_list_param = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5}
        with pytest.raises(ParameterTreeError) as excinfo:
            await test_param_tree.simple_list_tree.set('list_param', new_list_param)

        assert "Invalid path: list_param/4 list index out of range" in str(excinfo.value)

    async def test_bad_tuple_node_raises_error(self, test_param_tree):
        """Test that constructing a parameter tree with an immutable tuple raises an error."""
        bad_node = 'bad'
        bad_data = tuple(range(4))
        bad_tree = {
            bad_node: bad_data
        }
        with pytest.raises(ParameterTreeError) as excinfo:
            tree = AsyncParameterTree(bad_tree)

        assert "not a valid leaf node" in str(excinfo.value)

 
class AsyncRwParameterTreeTestFixture(AwaitableTestFixture):
    """Container class for use in async read-write parameter tree test fixtures."""

    def __init__(self):

        super(AsyncRwParameterTreeTestFixture, self).__init__(AsyncParameterTree)

        self.int_rw_param = 4576
        self.int_ro_param = 255374
        self.int_rw_value = 9876
        self.int_wo_param = 0

        self.rw_value_set_called = False

        self.nested_rw_param = 53.752
        self.nested_ro_value = 9.8765

        nested_tree = AsyncParameterTree({
            'nestedRwParam': (self.nestedRwParamGet, self.nestedRwParamSet),
            'nestedRoParam': self.nested_ro_value
        })

        self.rw_callable_tree = AsyncParameterTree({
            'intCallableRwParam': (self.intCallableRwParamGet, self.intCallableRwParamSet),
            'intCallableRoParam': (self.intCallableRoParamGet, None),
            'intCallableWoParam': (None, self.intCallableWoParamSet),
            'intCallableRwValue': (self.int_rw_value, self.intCallableRwValueSet),
            'branch': nested_tree
        })

    async def intCallableRwParamSet(self, value):
        await asyncio.sleep(0)
        self.int_rw_param = value

    async def intCallableRwParamGet(self):
        await asyncio.sleep(0)
        return self.int_rw_param

    async def intCallableRoParamGet(self):
        await asyncio.sleep(0)
        return self.int_ro_param

    async def intCallableWoParamSet(self, value):
        await asyncio.sleep(0)
        self.int_wo_param = value

    async def intCallableRwValueSet(self, value):
        await asyncio.sleep(0)
        self.rw_value_set_called = True

    async def nestedRwParamSet(self, value):
        await asyncio.sleep(0)
        self.nested_rw_param = value

    async def nestedRwParamGet(self):
        await asyncio.sleep(0)
        return self.nested_rw_param


@asyncio_fixture_decorator(scope="class")
async def test_rw_tree():
    """Test fixture for use in testing read-write parameter trees."""
    test_rw_tree = await AsyncRwParameterTreeTestFixture()
    yield test_rw_tree


@pytest.mark.asyncio
class TestAsyncRwParameterTree():
    """Class to test behaviour of async read-write parameter trees."""

    async def test_rw_tree_simple_get_values(self, test_rw_tree):
        """Test getting simple values from a RW tree returns the correct values."""
        dt_rw_int_param = await test_rw_tree.rw_callable_tree.get('intCallableRwParam')
        assert dt_rw_int_param['intCallableRwParam'] == test_rw_tree.int_rw_param

        dt_ro_int_param = await test_rw_tree.rw_callable_tree.get('intCallableRoParam')
        assert dt_ro_int_param['intCallableRoParam'] == test_rw_tree.int_ro_param

        dt_rw_int_value = await test_rw_tree.rw_callable_tree.get('intCallableRwValue')
        assert dt_rw_int_value['intCallableRwValue'] == test_rw_tree.int_rw_value

    async def test_rw_tree_simple_set_value(self, test_rw_tree):
        """Test that setting a value in a RW tree updates and returns the correct value."""
        new_int_value = 91210
        await test_rw_tree.rw_callable_tree.set('intCallableRwParam', new_int_value)

        dt_rw_int_param = await test_rw_tree.rw_callable_tree.get('intCallableRwParam')
        assert dt_rw_int_param['intCallableRwParam'] == new_int_value

    async def test_rw_tree_set_ro_param(self, test_rw_tree):
        """Test that attempting to set a RO parameter raises an error."""
        with pytest.raises(ParameterTreeError) as excinfo:
            await test_rw_tree.rw_callable_tree.set('intCallableRoParam', 0)

        assert 'Parameter intCallableRoParam is read-only' in str(excinfo.value)

    async def test_rw_callable_tree_set_wo_param(self, test_rw_tree):
        """Test that setting a write-only parameter (!!) sets the correct value."""
        new_value = 1234
        await test_rw_tree.rw_callable_tree.set('intCallableWoParam', new_value)
        assert test_rw_tree.int_wo_param == new_value

    async def test_rw_callable_tree_set_rw_value(self, test_rw_tree):
        """Test that setting a callable RW value calls the appropriate set method."""
        new_value = 1234
        await test_rw_tree.rw_callable_tree.set('intCallableRwValue', new_value)
        assert test_rw_tree.rw_value_set_called

    async def test_rw_callable_nested_param_get(self, test_rw_tree):
        """Test the getting a nested callable RW parameter returns the correct value."""
        dt_nested_param = await test_rw_tree.rw_callable_tree.get('branch/nestedRwParam')
        assert dt_nested_param['nestedRwParam'] == test_rw_tree.nested_rw_param

    async def test_rw_callable_nested_param_set(self, test_rw_tree):
        """Test that setting a nested callable RW parameter sets the correct value."""
        new_float_value = test_rw_tree.nested_rw_param + 2.3456
        await test_rw_tree.rw_callable_tree.set('branch/nestedRwParam', new_float_value)
        assert test_rw_tree.nested_rw_param == new_float_value

    async def test_rw_callable_nested_tree_set(self, test_rw_tree):
        """Test the setting a value within a callable nested tree updated the value correctly."""
        result = await test_rw_tree.rw_callable_tree.get('branch')
        nested_branch = result['branch']
        new_rw_param_val = 45.876
        nested_branch['nestedRwParam'] = new_rw_param_val
        await test_rw_tree.rw_callable_tree.set('branch', nested_branch)
        result = await test_rw_tree.rw_callable_tree.get('branch')
        assert result['branch']['nestedRwParam'], new_rw_param_val

    async def test_rw_callable_nested_tree_set_trailing_slash(self, test_rw_tree):
        """
        Test that setting a callable nested tree with a trailing slash in the path
        sets the value correctly.
        """
        result = await test_rw_tree.rw_callable_tree.get('branch/')
        nested_branch = result['branch']
        new_rw_param_val = 24.601
        nested_branch['nestedRwParam'] = new_rw_param_val
        await test_rw_tree.rw_callable_tree.set('branch/', nested_branch)
        result = await test_rw_tree.rw_callable_tree.get('branch/')
        assert result['branch']['nestedRwParam'] == new_rw_param_val


class AsyncParameterTreeMetadataTestFixture(AwaitableTestFixture):
    """Container class for use in test fixtures testing parameter tree metadata."""

    def __init__(self):

        super(AsyncParameterTreeMetadataTestFixture, self).__init__(AsyncParameterTree)

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
            'valueParam': (24601,),
            'minNoMaxParam': (1, {'min': 0})
        }
        self.metadata_tree = AsyncParameterTree(self.metadata_tree_dict)

    def intCallableRwParamSet(self, value):
        self.int_rw_param = value

    def intCallableRwParamGet(self):
        return self.int_rw_param

    def floatRoParamGet(self):
        return self.float_ro_param
    
    def intRoParamGet(self):
        return self.int_ro_param


@asyncio_fixture_decorator(scope="class")
async def test_tree_metadata():
    """Test fixture for use in testing parameter tree metadata."""
    test_tree_metadata = await AsyncParameterTreeMetadataTestFixture()
    yield test_tree_metadata

@pytest.mark.asyncio
class TestAsyncParameterTreeMetadata():

    async def test_callable_rw_param_metadata(self, test_tree_metadata):
        """Test that a getting RW parameter with metadata returns the appropriate metadata."""
        int_param_with_metadata = await test_tree_metadata.metadata_tree.get(
            "intCallableRwParam",with_metadata=True)
        result = await test_tree_metadata.metadata_tree.get("intCallableRwParam")
        int_param =  result["intCallableRwParam"]

        expected_metadata = test_tree_metadata.int_rw_param_metadata
        expected_metadata["value"] = int_param
        expected_metadata["type"] = 'int'
        expected_metadata["writeable"] = True
        expected_param = {"intCallableRwParam" : expected_metadata}
        
        assert int_param_with_metadata == expected_param

    async def test_get_filters_tree_metadata(self, test_tree_metadata):
        """
        Test that attempting to get a metadata field for a parameter as if it was path itself
        raises an error.
        """
        metadata_path = "name"
        with pytest.raises(ParameterTreeError) as excinfo:
            await test_tree_metadata.metadata_tree.get(metadata_path)

        assert "Invalid path: {}".format(metadata_path) in str(excinfo.value)

    async def test_set_tree_rejects_metadata(self, test_tree_metadata):
        """
        Test that attampeting to set a metadata field as if it was a parameter raises an error.
        """
        metadata_path = "name"
        with pytest.raises(ParameterTreeError) as excinfo:
            await test_tree_metadata.metadata_tree.set(metadata_path, "invalid")

        assert "Invalid path: {}".format(metadata_path) in str(excinfo.value)

    async def test_enum_param_allowed_values(self, test_tree_metadata):
        """Test that setting an enumerated parameter with an allowed value succeeds."""
        for value in test_tree_metadata.int_enum_param_allowed_values:
            await test_tree_metadata.metadata_tree.set("intEnumParam", value)
            result = await test_tree_metadata.metadata_tree.get("intEnumParam")
            set_value = result["intEnumParam"]
            assert value == set_value
    
    async def test_enum_param_bad_value(self, test_tree_metadata):
        """
        Test that attempting to set a disallowed value for an enumerated parameter raises an error.
        """
        bad_value = test_tree_metadata.int_enum_param_allowed_values[-1] + 1
        with pytest.raises(ParameterTreeError) as excinfo:
            await test_tree_metadata.metadata_tree.set("intEnumParam", bad_value)

        assert "{} is not an allowed value".format(bad_value) in str(excinfo.value)

    async def test_ro_param_has_writeable_metadata_field(self, test_tree_metadata):
        """Test that a RO parameter has the writeable metadata field set to false."""
        ro_param = await test_tree_metadata.metadata_tree.get("floatRoParam", with_metadata=True)
        assert ro_param["floatRoParam"]["writeable"] == False

    async def test_ro_param_not_writeable(self, test_tree_metadata):
        """Test that attempting to write to a RO parameter with metadata raises an error."""
        with pytest.raises(ParameterTreeError) as excinfo:
            await test_tree_metadata.metadata_tree.set("floatRoParam", 3.141275)
        assert "Parameter {} is read-only".format("floatRoParam") in str(excinfo.value)

    async def test_value_param_writeable(self, test_tree_metadata):
        """Test that a value parameter is writeable and has the correct metadata flag."""
        new_value = 90210
        await test_tree_metadata.metadata_tree.set("valueParam", new_value)
        result = await test_tree_metadata.metadata_tree.get("valueParam", with_metadata=True)
        set_param = result["valueParam"]
        assert set_param["value"] == new_value
        assert set_param["writeable"] == True

    async def test_rw_param_min_no_max(self, test_tree_metadata):
        """Test that a parameter with a minimum but no maximum works as expected."""
        new_value = 2
        await test_tree_metadata.metadata_tree.set("minNoMaxParam", new_value)
        result = await test_tree_metadata.metadata_tree.get("minNoMaxParam", with_metadata=True)
        set_param = result["minNoMaxParam"]
        assert set_param["value"] == new_value
        assert set_param["writeable"] == True

    async def test_rw_param_below_min_value(self, test_tree_metadata):
        """
        Test that attempting to set a value for a RW parameter below the specified minimum
        raises an error.
        """
        low_value = -1
        with pytest.raises(ParameterTreeError) as excinfo:
            await test_tree_metadata.metadata_tree.set("intCallableRwParam", low_value)

        assert "{} is below the minimum value {} for {}".format(
                low_value, test_tree_metadata.int_rw_param_metadata["min"], 
                "intCallableRwParam") in str(excinfo.value)

    async def test_rw_param_above_max_value(self, test_tree_metadata):
        """
        Test that attempting to set a value for a RW parameter above the specified maximum
        raises an error.
        """
        high_value = 100000
        with pytest.raises(ParameterTreeError) as excinfo:
            await test_tree_metadata.metadata_tree.set("intCallableRwParam", high_value)

        assert "{} is above the maximum value {} for {}".format(
                high_value, test_tree_metadata.int_rw_param_metadata["max"], 
                "intCallableRwParam") in str(excinfo.value)


class AsyncParameterTreeMutableTestFixture(AwaitableTestFixture):

    def __init__(self):

        super(AsyncParameterTreeMutableTestFixture, self).__init__(AsyncParameterTree)

        self.read_value = 64
        self.write_value = "test"

        self.param_tree_dict = {
            'extra': 'wibble',
            'bonus': 'win',
            'nest': {
                'double_nest': {
                    'nested_val': 125,
                    'dont_touch': "let me stay!",
                    'write': (self.get_write, self.set_write)
                },
                'list': [0, 1, {'list_test': "test"}, 3]
            },
            'read': (self.get_read,),
            'empty': {}
        }

        self.param_tree = AsyncParameterTree(self.param_tree_dict)
        self.param_tree.mutable = True

    async def get_read(self):
        return self.read_value

    async def get_write(self):
        return self.write_value

    async def set_write(self, data):
        self.write_value = data

@asyncio_fixture_decorator()
async def test_tree_mutable():
    """Test fixture for use in testing parameter tree metadata."""
    test_tree_mutable = await AsyncParameterTreeMutableTestFixture()
    yield test_tree_mutable

@pytest.mark.asyncio
class TestAsyncParamTreeMutable():
    """Class to test the behaviour of mutable async parameter trees"""

    async def test_mutable_put_differnt_data_type(self, test_tree_mutable):

        new_data = 75
        await test_tree_mutable.param_tree.set('bonus', new_data)
        val = await test_tree_mutable.param_tree.get('bonus')
        assert val['bonus'] == new_data

    async def test_mutable_put_new_branch_node(self, test_tree_mutable):

        new_node = {"new": 65}
        await test_tree_mutable.param_tree.set('extra', new_node)

        val = await test_tree_mutable.param_tree.get('extra')
        assert val['extra'] == new_node

    async def test_mutable_put_new_sibling_node(self, test_tree_mutable):

        new_node = {'new': 65}
        path = 'nest'

        await test_tree_mutable.param_tree.set(path, new_node)
        val = await test_tree_mutable.param_tree.get(path)
        assert 'new' in val[path]

    async def test_mutable_put_overwrite_param_accessor_read_only(self, test_tree_mutable):

        new_node = {"Node": "Broke Accessor"}
        with pytest.raises(ParameterTreeError) as excinfo:
            await test_tree_mutable.param_tree.set('read', new_node)
        
        assert "is read-only" in str(excinfo.value)

    async def test_mutable_put_overwrite_param_accessor_read_write(self, test_tree_mutable):

        new_node = {"Node": "Broke Accessor"}
        path = 'nest/double_nest/write'

        with pytest.raises(ParameterTreeError) as excinfo:
            await test_tree_mutable.param_tree.set(path, new_node)

        assert "Type mismatch setting" in str(excinfo.value)

    async def test_mutable_put_replace_nested_path(self, test_tree_mutable):

        new_node = {"double_nest": 294}
        path = 'nest'

        await test_tree_mutable.param_tree.set(path, new_node)
        val = await test_tree_mutable.param_tree.get(path)
        assert val[path]['double_nest'] == new_node['double_nest']

    async def test_mutable_put_merge_nested_path(self, test_tree_mutable):

        new_node = {
            "double_nest": {
                'nested_val': {
                    "additional_val": "New value Here!",
                    "add_int": 648
                }
            }
        }
        path = 'nest'

        await test_tree_mutable.param_tree.set(path, new_node)
        val = await test_tree_mutable.param_tree.get(path)
        assert val[path]['double_nest']['nested_val'] == new_node['double_nest']['nested_val']
        assert 'dont_touch' in val[path]['double_nest']

    async def test_mutable_delete_method(self, test_tree_mutable):

        path = 'nest/double_nest'

        test_tree_mutable.param_tree.delete(path)
        tree = await test_tree_mutable.param_tree.get('')
        assert 'double_nest' not in tree['nest']
        with pytest.raises(ParameterTreeError) as excinfo:
            await test_tree_mutable.param_tree.get(path)

        assert "Invalid path" in str(excinfo.value)

    async def test_mutable_delete_immutable_tree(self, test_tree_mutable):

        test_tree_mutable.param_tree.mutable = False

        with pytest.raises(ParameterTreeError) as excinfo:
            path = 'nest/double_nest'
            await test_tree_mutable.param_tree.delete(path)

        assert "Invalid Delete Attempt" in str(excinfo.value)

    async def test_mutable_delete_entire_tree(self, test_tree_mutable):

        path = ''

        test_tree_mutable.param_tree.delete(path)
        val = await test_tree_mutable.param_tree.get(path)
        assert not val

    async def test_mutable_delete_invalid_path(self, test_tree_mutable):

        path = 'nest/not_real'

        with pytest.raises(ParameterTreeError) as excinfo:
            await test_tree_mutable.param_tree.delete(path)

        assert "Invalid path" in str(excinfo.value)

    async def test_mutable_delete_from_list(self, test_tree_mutable):

        path = 'nest/list/3'

        test_tree_mutable.param_tree.delete(path)
        val = await test_tree_mutable.param_tree.get('nest/list')
        assert '3' not in val['list']

    async def test_mutable_delete_from_dict_in_list(self, test_tree_mutable):
        path = 'nest/list/2/list_test'

        test_tree_mutable.param_tree.delete(path)
        val = await test_tree_mutable.param_tree.get('nest/list')
        assert {'list_test': "test"} not in val['list']

    async def test_mutable_nested_tree_in_immutable_tree(self, test_tree_mutable):

        new_tree = await AsyncParameterTree({
            'immutable_param': "Hello",
            "nest": {
                "tree": test_tree_mutable.param_tree
            }
        })

        new_node = {"new": 65}
        path = 'nest/tree/extra'
        await new_tree.set(path, new_node)
        val = await new_tree.get(path)
        assert val['extra'] == new_node

    async def test_mutable_nested_tree_external_change(self, test_tree_mutable):

        new_tree = await AsyncParameterTree({
            'immutable_param': "Hello",
            "tree": test_tree_mutable.param_tree
        })

        new_node = {"new": 65}
        path = 'tree/extra'
        await test_tree_mutable.param_tree.set('extra', new_node)
        val = await new_tree.get(path)
        assert val['extra'] == new_node

    async def test_mutable_nested_tree_delete(self, test_tree_mutable):

        new_tree = await AsyncParameterTree({
            'immutable_param': "Hello",
            "tree": test_tree_mutable.param_tree
        })

        path = 'tree/bonus'
        new_tree.delete(path)

        tree = await new_tree.get('')

        assert 'bonus' not in tree['tree']

        with pytest.raises(ParameterTreeError) as excinfo:
            await test_tree_mutable.param_tree.get(path)

        assert "Invalid path" in str(excinfo.value)

    async def test_mutable_nested_tree_root_tree_not_affected(self, test_tree_mutable):

        new_tree = await AsyncParameterTree({
            'immutable_param': "Hello",
            "nest": {
                "tree": test_tree_mutable.param_tree
            }
        })

        new_node = {"new": 65}
        path = 'immutable_param'

        with pytest.raises(ParameterTreeError) as excinfo:
            await new_tree.set(path, new_node)

        assert "Type mismatch" in str(excinfo.value)

    async def test_mutable_add_to_empty_dict(self, test_tree_mutable):

        new_node = {"new": 65}
        path = 'empty'
        await test_tree_mutable.param_tree.set(path, new_node)
        val = await test_tree_mutable.param_tree.get(path)
        assert val[path] == new_node