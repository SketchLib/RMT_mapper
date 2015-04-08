from rmt_configuration import RmtConfiguration
from rmt_greedy_compiler import RmtGreedyCompiler
import numpy as np
import logging

import math
import operator
import parser
#import pydot
import sys

from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph
from pygraph.algorithms.minmax import shortest_path
#from pygraph.readwrite.dot import write

from rmt_dependency_analysis import RmtDependencyAnalysis

class RmtFflCompiler(RmtGreedyCompiler):
    def __init__(self, numSramBlocksReserved=0):
        RmtGreedyCompiler.__init__(self, numSramBlocksReserved, version="FFL")
        self.logger = logging.getLogger(__name__)
        pass

    def getOrderedTables(self):
        dependencyAnalysis = RmtDependencyAnalysis(self.program)
        progInfo = dependencyAnalysis.getPerLogProgramInfo()
        tables = progInfo.keys()
        # tables farthest from end first
        backLengths = [(t, progInfo[t]['distanceFromEnd']) for t in tables]
        backLengths = sorted(backLengths, key= lambda pair: pair[1], reverse=True)
        self.orderedTables = backLengths
        self.logger.info("tables in order of level (distance from end)")
        string = ""
        for o,t in self.orderedTables:
            string += o + "(" + str(t) + "), "
            pass
        self.logger.info(string)
        pass
    pass
