"""
Test cases for the ExcaliburDetector class of the ODIN server EXCALIBUR plugin

Tim Nicholls, STFC Application Engineering Group
"""

from nose.tools import *
import logging

from excalibur.detector import ExcaliburDetector, ExcaliburDetectorError


class TestExcaliburDetector():

    @classmethod
    def setup_class(cls):
        cls.detector_fems = [('192.168.0.1', 6969), ('192.168.0.2', 6969), ('192.168.0.3', 6969)]
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

    def test_detector_simple_init(self):

        detector = ExcaliburDetector(self.detector_fems)
        assert_equal(len(detector.fems), len(self.detector_fems))

    def test_detector_single_fem(self):

        detector = ExcaliburDetector(self.detector_fems[0])
        assert_equal(len(detector.fems), 1)

    def test_detector_bad_fem_spec(self):

        with assert_raises_regexp(ExcaliburDetectorError, "Failed to initialise detector FEM list"):
            detector = ExcaliburDetector([1, 2, 3])

        with assert_raises_regexp(ExcaliburDetectorError, "Failed to initialise detector FEM list"):
            detector = ExcaliburDetector('nonsense')

    def test_detector_bad_fem_port(self):
        bad_detector_fems = self.detector_fems[:]
        bad_detector_fems[0] = ('192.168.0.1', 'bad_port')

        with assert_raises_regexp(ExcaliburDetectorError, "Failed to initialise detector FEM list"):
            detector = ExcaliburDetector(bad_detector_fems)

    def test_detector_connect_fems(self):

        detector = ExcaliburDetector(self.detector_fems)
        detector.connect()
