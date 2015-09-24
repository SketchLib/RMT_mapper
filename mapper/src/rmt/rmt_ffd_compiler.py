#
# Copyright (c) 2015-2016 by The Board of Trustees of the Leland
# Stanford Junior University.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
#  Author: Lavanya Jose (lavanyaj@cs.stanford.edu)
#
#



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
        """ Return tables in order of limiting resource- if a table needs 2 out 8 available input xbar units
        and 512 of say 1024 available bits of the action data xbar (in every stage), then action data xbar
        is the limiting resources, since it need 50% of the available resource per stage
        (vs 25% for input xbar). """
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
