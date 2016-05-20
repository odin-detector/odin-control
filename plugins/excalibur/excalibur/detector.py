"""EXCALIBUR detector implementation for the ODIN EXCALIBUR plugin.

Tim Nicholls, STFC Application Engineering
"""

import logging
from excalibur.fem import ExcaliburFem, ExcaliburFemError


class ExcaliburDetectorError(Exception):
    """Simple exception class for ExcaliburDetector."""

    pass


class ExcaliburDetector(object):
    """EXCALIBUR detector class.

    This class implements the representation of an EXCALIBUR detector, providing the composition
    of one or more ExcaliburFem instances into a complete detector.
    """

    def __init__(self, fem_connections):
        """Initialise the ExcaliburDetector object.

        :param fem_connections: list of (address, port) FEM connections to make
        """
        if not isinstance(fem_connections, list):
            fem_connections = [fem_connections]
        print fem_connections, type(fem_connections)

        idx = 1
        for (host, port) in fem_connections:
            logging.info("%d: %s:%d", idx, host, port)
            print(idx, host, port)
            idx += 1
