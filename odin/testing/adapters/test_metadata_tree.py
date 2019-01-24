"""Test MetadataParameterTree class from odin

James Hogge, STFC Applications Engineering Group
"""


from nose.tools import *
from odin.adapters.metadata_tree import MetadataTree, MetadataParameterError

class TestMetadataTree():
    """Test class for MetadataTree
    """

    @classmethod
    def setup_class(cls):

        cls.basic_dict = {
            "int" : 0,
            "float" : 3.14,
            "string" : "hello world",
            "bool" : True
        }
        cls.basic_tree = MetadataTree(cls.basic_dict)

        cls.nested_dict = cls.basic_dict.copy()
        cls.nested_dict["dict"] = {"0" : 0, "1" : 1}
        cls.nested_tree = MetadataTree(cls.nested_dict)

        cls.list_dict = {
            "even" : [2,4,6,8, 10],
            "prime" : [2,3,5,7,11]
        }
        cls.list_tree = MetadataTree(cls.list_dict)

        cls.accessor_dict = {
            "value" : (0,),
            "metadata_value0" : (0, {"writeable" : False}),
            "metadata_value1" : ("not running", {"available" : ["not running", "pending", "running", "completed"]}),
            "getter" : (cls.getA),
            "getter_setter" : (cls.getB, cls.setB),
            "getter_metadata" : (cls.getC, {"units" : "s"}),
            "getter_setter_metadata" : (cls.getB, cls.setB, {"min" : 0, "max" : 100})
        }
        cls.accessor_tree = MetadataTree(cls.accessor_dict)

    def test_basic_get(self):
        assert_equal(self.basic_tree.get(""), self.basic_dict)

    def test_basic_value_get(self):
        assert_equal(self.basic_tree.get("int"), {"int" : self.basic_dict["int"]})

    def test_basic_value_set(self):
        self.basic_tree.set("bool", False)
        assert_equal(self.basic_tree.get("bool"), {"bool" : False})
        self.basic_dict["bool"] = False

    def test_basic_root_set(self):
        self.basic_tree.set("", {"int" : 1, "string" : "test"})
        self.basic_dict["int"] = 1
        self.basic_dict["string"] = "test"
        assert_equal(self.basic_tree.get(""), self.basic_dict)

    def test_basic_auto_metadata(self):
        metadata = {
            "int" : {"value" : self.basic_dict["int"], "type" : "int", "writeable" : True, "dp": 2},
            "float" : {"value" : self.basic_dict["float"], "type" : "float", "writeable" : True, "dp": 2},
            "string" : {"value" : self.basic_dict["string"], "type" : "str", "writeable" : True},
            "bool" : {"value" : self.basic_dict["bool"], "type" : "bool", "writeable" : True}
        }
        assert_equal(self.basic_tree.get("", metadata=True), metadata)

    def test_basic_missing_path(self):
        with assert_raises_regexp(MetadataParameterError, "Invalid path: "):
            self.basic_tree.get("missing")

    def test_basic_try_change_value_type(self):
        with assert_raises_regexp(MetadataParameterError, "Type mismatch updating"):
            self.basic_tree.set("int", "error")

    def test_nested_root_get(self):
        assert_equal(self.nested_dict, self.nested_tree.get(""))

    def test_nested_specific_get(self):
        assert_equal({"dict" : self.nested_dict["dict"]}, self.nested_tree.get("dict"))

    def test_nested_metadata(self):
        metadata = {
            "int" : {"value" : self.nested_dict["int"], "type" : "int", "writeable" : True, "dp": 2},
            "float" : {"value" : self.nested_dict["float"], "type" : "float", "writeable" : True, "dp": 2},
            "string" : {"value" : self.nested_dict["string"], "type" : "str", "writeable" : True},
            "bool" : {"value" : self.nested_dict["bool"], "type" : "bool", "writeable" : True},
            "dict" : {
                "0" : {"value" : self.nested_dict["dict"]["0"], "type" : "int", "writeable" : True, "dp": 2},
                "1" : {"value" : self.nested_dict["dict"]["1"], "type" : "int", "writeable" : True, "dp": 2}
            }
        }
        print(self.nested_tree.get("", metadata=True))
        assert_equal(self.nested_tree.get("", metadata=True), metadata)

    def test_nested_try_inject_dict(self):
        with assert_raises_regexp(MetadataParameterError, "Merging error: "):
            self.nested_tree.set("", {"int" : {"a": 0, "b": 1}})

    def test_list_root_get(self):
        assert_equal(self.list_dict, self.list_tree.get(""))

    def test_list_index_get(self):
        assert_equal(self.list_tree.get("even/2"), {"2" : 6})

    def test_list_index_set(self):
        self.list_tree.set("prime/0", 1)
        self.list_dict["prime"][0] = 1
        assert_equal(self.list_tree.get(""), self.list_dict)

    def test_list_whole_set(self):
        self.list_tree.set("prime", [13, 17, 19, 23, 29])
        self.list_dict["prime"] = [13, 17, 19, 23, 29]
        assert_equal(self.list_tree.get("prime"), {"prime" : self.list_dict["prime"]})

    def test_list_out_of_range(self):
        with assert_raises_regexp(MetadataParameterError, "Invalid path: "):
            self.list_tree.get("prime/5")



    @classmethod
    def getA(cls):
        return 2.718

    _value = 0
    _called_setb = False
    @classmethod
    def getB(cls):
        return cls._value
    @classmethod
    def setB(cls, value):
        cls._value = value
        cls._called_setb = True

    @classmethod
    def getC(cls):
        return False
        
    def test_accessor_value_get(self):
        assert_equal(self.accessor_tree.get("value"), {"value" : self.accessor_dict["value"][0]})

    def test_accessor_value_set(self):
        self.accessor_tree.set("value", 17)
        assert_equal(self.accessor_tree.get("value"), {"value" : 17})

    def test_accessor_value0_metadata(self):
        metadata = {"metadata_value0" : {"value" : 0, "type" : "int", "writeable" : False, "dp": 2}}
        assert_equal(self.accessor_tree.get("metadata_value0", metadata=True), metadata)

    def test_accessor_try_write_to_read_only(self):
        with assert_raises_regexp(MetadataParameterError, "Parameter metadata_value0 is read-only"):
            self.accessor_tree.set("metadata_value0", 1)

    def test_accessor_set_invalid_option(self):
        with assert_raises_regexp(MetadataParameterError, "test is not an allowed value for metadata_value1"):
            self.accessor_tree.set("metadata_value1", "test")

    def test_accessor_set_valid_option(self):
        self.accessor_tree.set("metadata_value1", "running")
        assert_equal(self.accessor_tree.get("metadata_value1"), {"metadata_value1" : "running"})

    def test_accessor_getter(self):
        assert_equal(self.accessor_tree.get("getter"), {"getter" : 2.718})

    def test_accessor_getter_setter(self):
        TestMetadataTree._called_setb = False
        self.accessor_tree.set("getter_setter", 2)
        assert_equal(self.accessor_tree.get("getter_setter"), {"getter_setter" : 2})
        assert_equal(self._called_setb, True)

    def test_accessor_getter_metadata(self):
        metadata = {"getter_metadata" : {"value" : False, "type" : "bool", "writeable" : False, "units" : "s"}}
        assert_equal(self.accessor_tree.get("getter_metadata", metadata=True), metadata)

    def test_accessor_try_write_out_of_range(self):
        with assert_raises_regexp(MetadataParameterError, "-1 is below the minimum value 0 for getter_setter_metadata"):
            self.accessor_tree.set("getter_setter_metadata", -1)
        with assert_raises_regexp(MetadataParameterError, "101 is above the maximum value 100 for getter_setter_metadata"):
            self.accessor_tree.set("getter_setter_metadata", 101)

    def test_accessor_create_error(self):
        with assert_raises_regexp(MetadataParameterError, ".+ is not a valid leaf node"):
            MetadataTree({"error" : ()})

        with assert_raises_regexp(MetadataParameterError, ".+ is not a valid leaf node"):
            MetadataTree({"error" : (TestMetadataTree.getA, TestMetadataTree.getB, [0,1,2])})

    def test_accessor_invalid_kwarg(self):
        with assert_raises_regexp(MetadataParameterError, "Invalid argument: "):
            MetadataTree({"error" : (1, {"units" : "m", "invalid_kwarg" : "test"})}) 
