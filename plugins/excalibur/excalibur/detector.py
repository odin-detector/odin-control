"""EXCALIBUR detector implementation for the ODIN EXCALIBUR plugin.

Tim Nicholls, STFC Application Engineering
"""

import logging
from excalibur.fem import ExcaliburFem, ExcaliburFemError


class ExcaliburDetectorError(Exception):
    """Simple exception class for ExcaliburDetector."""

    pass


class ExcaliburDetectorFemConnection(object):
    """Internally used container class describing FEM connection."""

    STATE_DISCONNECTED = 0
    STATE_CONNECTED = 1

    def __init__(self, id, host, port, fem=None, state=STATE_DISCONNECTED):

        self.id = id
        self.host = host
        self.port = port
        self.fem = fem
        self.state = self.STATE_DISCONNECTED


class ExcaliburDetector(object):
    """EXCALIBUR detector class.

    This class implements the representation of an EXCALIBUR detector, providing the composition
    of one or more ExcaliburFem instances into a complete detector.
    """

    def __init__(self, fem_connections):
        """Initialise the ExcaliburDetector object.

        :param fem_connections: list of (address, port) FEM connections to make
        """
        self.fems = []
        if not isinstance(fem_connections, (list, tuple)):
            fem_connections = [fem_connections]
        if isinstance(fem_connections, tuple) and len(fem_connections) == 2:
            fem_connections = [fem_connections]

        try:
            id = 1
            for (host, port) in fem_connections:
                self.fems.append(ExcaliburDetectorFemConnection(id, host, int(port)))
                id += 1
        except Exception as e:
            raise ExcaliburDetectorError('Failed to initialise detector FEM list: {}'.format(e))

    def connect(self):
        """Establish connection to the detectors FEMs."""
        for idx in range(len(self.fems)):
            the_fem = ExcaliburFem(self.fems[idx].id)
            self.fems[idx].fem = the_fem
