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

class RmtFfdCompiler(RmtGreedyCompiler):
    def __init__(self, numSramBlocksReserved=0):
        RmtGreedyCompiler.__init__(self, numSramBlocksReserved, version="FFD")
        self.logger = logging.getLogger(__name__)
        pass
    
    def getLimitingResourceUse(self, table):
        if table == 'start' or table == 'end':
            return 0
        
        tableIndex = self.getIndex(table, self.program.names)
        fracSubunits = [float(self.getInputCrossbarSubunits(tableIndex,mem))\
                            /self.getMaximumInputCrossbarSubunits(tableIndex,mem) for mem\
                            in self.getMem(tableIndex)]
        # One action data xbar for both mems
        fracWidthActionData = [float(self.getWidthActionData(tableIndex))\
                                   /self.getMaximumWidthActionData(tableIndex,mem) for mem\
                                   in self.getMem(tableIndex)[:1]]
        self.logger.debug("Resources for " + self.program.names[tableIndex]\
                         + ": " + str(fracSubunits) + " for input crossbar"\
                         + " and " + str(fracWidthActionData) + " for action data bits")
        
        return max(max(fracSubunits), max(fracWidthActionData))
        # Number of SRAM blocks (entries) is not a "resource"
        
        pass

    def getOrderedTables(self):
        tables = self.gr.nodes()        
        limitingResource = [(t, self.getLimitingResourceUse(t)) for t in tables]
        limitingResource = sorted(limitingResource, key= lambda pair: pair[1], reverse=True)
        self.orderedTables = limitingResource #sorted(limitingResource, key= lambda pair: distFromStart[pair[0]])
        string = "tables in order of limiting resource"
        for o,t in self.orderedTables:
            string += o + "(" + str(t) + "), "
            pass
        self.logger.info(string)

        pass
    pass
