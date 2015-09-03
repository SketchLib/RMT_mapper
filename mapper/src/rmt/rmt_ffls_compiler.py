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

from rmt_dependency_analysis import RmtDependencyAnalysis

class RmtFflsCompiler(RmtGreedyCompiler):
    def __init__(self, numSramBlocksReserved=0):
        RmtGreedyCompiler.__init__(self, numSramBlocksReserved, version="FFLS")
        self.logger = logging.getLogger(__name__)

        pass

    def getNumStages(self, tableIndex):
        numWordsLeft = int(self.program.logicalTables[tableIndex])
        mems = self.getMem(tableIndex)

        st = 0
        m = 0
        lastBlock = {}
        for mem in self.switch.memoryTypes:
            lastBlock[mem] = -1
            pass
        
        while (numWordsLeft > 0):
            fit = self.getBestFitForBlocks(tableIndex, mems[m],
                                           lastBlock=lastBlock, numSramBlocksReserved=0)
            if fit['numMatchWords'] == 0:
                name = self.program.names[tableIndex]
                self.logger.info("getBestFitForBlocks: Can't fit any words of %s in st %d" % (name, st))
                pass

            
            if fit['numMatchWords'] > numWordsLeft:
                fit = self.getBestFitForWords(tableIndex, mems[m],\
                                                  lastBlock=lastBlock,\
                                                  numWordsLeft=numWordsLeft)

                if fit['numMatchWords'] == 0:
                    name = self.program.names[tableIndex]
                    self.logger.info("getBestFitForWords: Can't fit any words of %s in st %d" % (name, st))
                    pass

                pass

            if fit['numMatchWords'] > 0:            
                lastBlock[mems[m]] += fit['numMatchBlocks']
                lastBlock['sram'] += fit['numActionBlocks']
                numWordsLeft -= min(numWordsLeft, fit['numMatchWords'])
                pass
            
            if numWordsLeft == 0:
                continue

            m = (m + 1)%len(mems)
            if m == 0:
                st += 1
                lastBlock = {}
                for mem in self.switch.memoryTypes:
                    lastBlock[mem] = -1
                    pass
                pass
            pass
        lastStageInfo = ",".join(["%d %ss" % (lastBlock[mem]+1, mem.upper()) for mem in\
                                      self.switch.memoryTypes])
        numStages = st

        self.logger.info("%s needs %d stages plus  %s" %\
                         (self.program.names[tableIndex], st, lastStageInfo))

        return numStages

    
    def getOrderedTables(self):
        self.logger.info("Number of stages taken by each table")
        logMax = self.program.MaximumLogicalTables
        tableWeights = {}
        for log in range(logMax):
            name = self.program.names[log]
            numStages = self.getNumStages(log)
            tableWeights[name] = numStages
            pass
        self.logger.info("Table weights: %s" % tableWeights)
        
        da = RmtDependencyAnalysis(self.program)
        programInfo = da.getPerLogProgramInfo(tableWeights)

        weightedGr = da.addWeights(da.flipEdgeSign(da.getDigraph()), tableWeights)
        edgeInfo =    ",".join(["%s: %s, " % (edge, weightedGr.edge_weight(edge)) for edge in weightedGr.edges()])
        self.logger.debug("Edge weights in weighted graph: %s" % edgeInfo)

        
        gr = da.reverseEdges(weightedGr)
        self.logger.info("\nCritical path in weighted graph: %s" % da.showPath(da.showCriticalPath(gr)))
        
        tables = programInfo.keys()
        # tables farthest from end first

        sortedTables = {}
        orderedTables = {}
        for sortKey in ['distanceFromEnd', 'distanceFromEndWeighted']:
            sortedTables[sortKey] = sorted(tables,\
                                      key = lambda t: programInfo[t][sortKey],\
                                      reverse=True)
            orderedTables[sortKey] =\
                [(t, programInfo[t][sortKey]) for t in sortedTables[sortKey]]
        
            self.logger.info("tables in order of %s: %s" % (sortKey, sortedTables[sortKey]))
            pass

        for table in sortedTables['distanceFromEnd']:
            self.logger.info("Table %s: dist. from end is %d, .. weighted is %.2f" %\
                             (table, programInfo[table]['distanceFromEnd'],\
                                  programInfo[table]['distanceFromEndWeighted']))
            pass
        
        self.orderedTables = orderedTables['distanceFromEndWeighted']
        string = ""
        for o,t in self.orderedTables:
            string += o + "(" + str(t) + "), "
            pass
        self.logger.info(string)
        pass
    pass
