"""
Test cases for the ExcaliburDetector class of the ODIN server EXCALIBUR plugin

Tim Nicholls, STFC Application Engineering Group
"""

from nose.tools import *

from excalibur.detector import ExcaliburDetector, ExcaliburDetectorError


class TestExcaliburDetector():

    @classmethod
    def setup_class(cls):
        cls.detector_fems = [('192.168.0.1', 6969), ('192.168.0.2', 6969), ('192.168.0.3', 6969)]

    def test_detector_simple_init(self):

        detector = ExcaliburDetector(self.detector_fems)
        print detector

    def test_detector_single_fem(self):

        detector = ExcaliburDetector(self.detector_fems[0])
        print detector

    # def test_detector_bad_fem_spec(self):
    #
    #     detector = ExcaliburDetector([1, 2, 3])
    #     print detector
