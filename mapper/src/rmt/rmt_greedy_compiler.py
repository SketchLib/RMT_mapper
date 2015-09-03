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
from rmt_dependency_analysis import RmtDependencyAnalysis

import numpy as np
import time
import logging

import math
import operator
import parser
#import pydot
import sys

from pygraph.classes.digraph import digraph
#from pygraph.readwrite.dot import write

class RmtGreedyCompiler:
    def __init__(self, numSramBlocksReserved=0, version=None):
        self.numSramBlocksReserved = numSramBlocksReserved
        self.version = version
        self.logger = logging.getLogger(__name__)
        pass

    def getIndex(self, table, names):
        i = 0
        for name in names:
            if table == name:
                return i
            i += 1
            pass
        self.logger.warn(table + " not found in names.")
        return len(names)

    def getBestFitForWords(self, tableIndex, mem, lastBlock, numWordsLeft):
        perPf = {'match': self.getPerPf(mem=mem, tableIndex=tableIndex),\
                     'action': self.getPerPf(mem='action', tableIndex=tableIndex)}

        # Just have one 'packing unit' option for action memory.
        pfAction = 0
        
        hasAction = int(perPf['action']['words'][pfAction] > 0)
        inTcam = int(mem == 'tcam')
        inSram = int(mem == 'sram')

        numBlocksLeft = self.blocksPerSt[mem] - (lastBlock[mem] + 1)
        numBlocksSramLeft = self.blocksPerSt['sram'] - (lastBlock['sram'] + 1)
        numBlocksTcamLeft = self.blocksPerSt['tcam'] - (lastBlock['tcam'] + 1) 

        numWords = {}
        numPUnits = {}
        numBlocks = {}
        for thing in ['Match','Action']:
            numWords[thing] = 0
            numPUnits[thing] = 0
            numBlocks[thing] = 0
            pass
        # Choosing best 'packing unit' option, that uses minimum number of blocks
        # in this stage.
        allMatchPfs = range(len(perPf['match']['blocks']))
        paramsForPf = {}

        for pfMatch in allMatchPfs:
            # Some packing units can't store any words e.g., a one RAM wide
            # packing unit can't store a 160b entry, ideally preprocessor
            # shouldn't pass in these options.
            if perPf['match']['words'][pfMatch] <= 0:
                continue

            # Lower bound on number of match packing units we could fit in.
            numPUnits['Match'] = int(math.ceil(float(numWordsLeft)/perPf['match']['words'][pfMatch]))

            # MATCH
            numBlocks['Match'] = numPUnits['Match'] * perPf['match']['blocks'][pfMatch]
            numWords['Match'] = numPUnits['Match'] * perPf['match']['words'][pfMatch]

            """
            if numMatchBlocks >= numBlocks:
                continue
            """

            # ACTION
            numPUnits['Action'] = 0
            if hasAction:
                numPUnits['Action'] = int(math.ceil(float(numWords['Match'])/perPf['action']['words'][pfAction]))
                pass
            self.logger.debug("hasAction: %d, numPUnits['Action']: %d" % (hasAction, numPUnits['Action']))
            self.logger.debug("perPfActionWords: %f, perPfActionBlocks: %f" % (perPf['action']['words'][pfAction],\
                                                                           perPf['action']['blocks'][pfAction]))
            numWords['Action'] = numPUnits['Action'] * perPf['action']['words'][pfAction]
            numBlocks['Action'] = numPUnits['Action'] * perPf['action']['blocks'][pfAction]
            self.logger.debug("numWords['Action']: %f, numBlocks['Action']: %f" % (numWords['Action'], numBlocks['Action']))
            

            # CHECK if there's enough RAMs/ TCAMs for match and action.
            if not(\
                numBlocks['Action'] +  numBlocks['Match'] * inSram  <= numBlocksSramLeft and\
                    numBlocks['Match'] <= numBlocksLeft):
                continue
            else:
                pfFor = {'Match': pfMatch, 'Action': pfAction}
                paramsForPf[pfMatch] = {}
                for thing in (['Match', 'Action']):
                    paramsForPf[pfMatch]['num%sWords'%thing] = numWords[thing]
                    paramsForPf[pfMatch]['num%sPUnits'%thing] = numPUnits[thing]
                    paramsForPf[pfMatch]['num%sBlocks'%thing] = numBlocks[thing]
                    paramsForPf[pfMatch]['pf%s'%thing] = pfFor[thing]
                    pass
                pass
            pass

        emptyParams = {}
        for thing in (['Match', 'Action']):
            emptyParams['num%sWords'%thing] = 0
            emptyParams['num%sPUnits'%thing] =0
            emptyParams['num%sWords'%thing] = 0
            emptyParams['pf%s'%thing] = 0
            pass

        # For some pf, should have enough memory for everything, else wouldn't be here
        # return blocksMin, pfBlocks, iMin
        if (len(paramsForPf) > 0):
            best_pf = min(paramsForPf.keys(), key=lambda pf: paramsForPf[pf]['numMatchBlocks'])
            returnValue = paramsForPf[best_pf]
        else:
            returnValue = emptyParams
            pass

        self.logger.debug("Returning from bestFitForWords: pf " + str(returnValue))
        return returnValue

    def getPerPf(self, mem, tableIndex):
        shape = self.blocksPerPf[mem][tableIndex].shape
        perPf = {}
        if shape[0] == 1 and shape[1] == 1:
            perPf['blocks'] = [self.blocksPerPf[mem][tableIndex]]
            perPf['words'] = [self.wordsPerPf[mem][tableIndex]]
            pass
        else:
            perPf['blocks'] = self.blocksPerPf[mem][tableIndex]
            perPf['words'] = self.wordsPerPf[mem][tableIndex]
            pass
        return perPf
        
    def getBestFitForBlocks(self, tableIndex, mem, lastBlock, numSramBlocksReserved):
        perPf = {'match': self.getPerPf(mem=mem, tableIndex=tableIndex),\
                     'action': self.getPerPf(mem='action', tableIndex=tableIndex)}
        # Just have one 'packing unit' option for action memory.
        pfAction = 0


        hasAction = int(perPf['action']['words'][pfAction] > 0)
        inTcam = int(mem == 'tcam')
        inSram = int(mem == 'sram')

        numBlocksLeft = self.blocksPerSt[mem] - (lastBlock[mem] + 1)
        numBlocksSramLeft = self.blocksPerSt['sram'] - (lastBlock['sram'] + 1)
        numBlocksTcamLeft = self.blocksPerSt['tcam'] - (lastBlock['tcam'] + 1)

        self.logger.debug("%s blocks per stage: %d" % (mem, self.blocksPerSt[mem]))
        self.logger.debug("number of " + mem + " blocks left " + str(int(numBlocksLeft)))
        self.logger.debug("number of SRAM blocks left " + str(int(numBlocksSramLeft)))

        numWords = {}
        numPUnits = {}
        numBlocks = {}
        for thing in ['Match','Action']:
            numWords[thing] = 0
            numPUnits[thing] = 0
            numBlocks[thing] = 0
            pass
        # Choosing best 'packing unit' option, that allows maximum match entries
        # in this stage.
        allMatchPfs = range(len(perPf['match']['blocks']))
        paramsForPf = {}



        for pfMatch in allMatchPfs:
            # Some packing units can't store any words e.g., a one RAM wide
            # packing unit can't store a 160b entry, ideally preprocessor
            # shouldn't pass in these options.
            if perPf['match']['words'][pfMatch] <= 0:
                self.logger.info("getBestFitForBlocks: can't use any match %d-word packing units" % (perPf['match']['words'][pfMatch]))
                continue

            # Upper bound on number of match packing units we could fit in.
            numPUnits['Match'] = int(math.floor(float(numBlocksLeft)/perPf['match']['blocks'][pfMatch]))

            if numPUnits['Match'] == 0:
                self.logger.debug("getBestFitForBlocks: can't fit any match %d-RAM packing units in %d blocks" % (perPf['match']['blocks'][pfMatch],\
                                                                                                                 numBlocksLeft))
                continue

            numWords['Match'] = numPUnits['Match'] * perPf['match']['words'][pfMatch]
            numBlocks['Match'] = numPUnits['Match'] * perPf['match']['blocks'][pfMatch]
            # Find the right combination of action RAMs, match memory
            # that fits in available SRAM, TCAM.
            
            while(numPUnits['Match'] > 0):
                # MATCH
                numWords['Match'] = numPUnits['Match'] * perPf['match']['words'][pfMatch]
                numBlocks['Match'] = numPUnits['Match'] * perPf['match']['blocks'][pfMatch]

                # ACTION
                numPUnits['Action'] = 0
                if hasAction:
                    numPUnits['Action'] = int(math.ceil(float(numWords['Match'])/perPf['action']['words'][pfAction]))
                    pass
                numWords['Action'] = numPUnits['Action'] * perPf['action']['words'][pfAction]
                numBlocks['Action'] = numPUnits['Action'] * perPf['action']['blocks'][pfAction]

                
                # CHECK if there's enough RAMs/ TCAMs for match and action.
                # If assigning match blocks in SRAM, exclude numSramBlocksReserved
                if numBlocks['Action'] +  numBlocks['Match'] * inSram <=\
                        numBlocksSramLeft - inSram * numSramBlocksReserved and\
                        numBlocks['Match'] <= numBlocksLeft:
                    self.logger.info("Found a config. that fits using %d-wide packing units: %d match, %d action" %\
                                     (perPf['match']['blocks'][pfMatch], numBlocks['Match'], numBlocks['Action']))
                    break

                numPUnits['Match'] -= 1
                pass

            if numPUnits['Match'] <= 0 or numWords['Match'] <= 0:
                continue

            paramsForPf[pfMatch] = {}
            pfFor = {'Match': pfMatch, 'Action': pfAction}
            for thing in (['Match', 'Action']):
                paramsForPf[pfMatch]['num%sWords'%thing] = numWords[thing]
                paramsForPf[pfMatch]['num%sPUnits'%thing] = numPUnits[thing]
                paramsForPf[pfMatch]['num%sBlocks'%thing] = numBlocks[thing]
                paramsForPf[pfMatch]['pf%s'%thing] = pfFor[thing]
                pass
            pass

        emptyParams = {}
        for thing in (['Match', 'Action']):
            emptyParams['num%sWords'%thing] = 0
            emptyParams['num%sPUnits'%thing] =0
            emptyParams['num%sWords'%thing] = 0
            emptyParams['num%sBlocks'%thing] = 0
            emptyParams['pf%s'%thing] = 0
            pass

        if (len(paramsForPf) > 0):
            best_pf = max(paramsForPf.keys(), key=lambda pf: paramsForPf[pf]['numMatchWords'])
            returnValue = paramsForPf[best_pf]

        else:
            self.logger.info("Returning empty params.")
            returnValue = emptyParams
            pass

        self.logger.debug("Returning from bestFitForBlocks: pf " + str(returnValue))
        return returnValue

    
    def getNextTable(self):
        succWeight = 0
#        self.logger.debug("Looking for next table")
        for table,dist in self.orderedTables:
            if table not in self.assigned:
                self.logger.debug("Table " + table + "?")
                previousTables = self.gr.neighbors(table)
                self.logger.debug("Must assign " + str(previousTables) + " first")
                leftToAssign = len(previousTables)
                for prev in previousTables:
                    if prev in self.assigned:
                        leftToAssign -= 1
                        pass
                    pass
                if leftToAssign == 0:                    
                    earliestStage = [self.assigned[prev]\
                                         + int(abs(self.gr.edge_weight((table,prev))))\
                                         for prev in previousTables]
                    earliestStages = [(self.assigned[prev],\
                                           self.assigned[prev] + int(abs(self.gr.edge_weight((table,prev)))),\
                                           prev) for prev in previousTables]
                    earliestStages = sorted(earliestStages, key = lambda tup: tup[1], reverse=True)
                    self.logger.debug("Earliest stage for %s must be at least %s" % (table, earliestStages))
                    return table, max(earliestStage)
                pass
            pass
        self.logger.warn("No table left that can be assigned.")
        return None

    # Advances last block for respective memory to last block before
    # earliest stage. (default to last block of current stage.)
    # Also resets input crossbar, action crossbar for the memory to 0
    # (since this is the first time we're using mem, earliest stage)

    def getMem(self, tableIndex):
        validMems = []
        self.logger.debug("mems in self.preprocess.use %s" % str(self.preprocess.use.keys()))
        self.logger.debug("self.preprocess.use['sram'] %s" % str(self.preprocess.use['sram']))
        for mem in self.preprocess.use:
            if self.preprocess.use[mem][tableIndex] == 1\
                    and mem in self.switch.numSlices:
                validMems.append(mem)
                pass
            pass
        return validMems
    
    def  getInputCrossbarSubunits(self, tableIndex, mem):
        return self.preprocess.inputCrossbarNumSubunits[mem][tableIndex]

    def getMaximumInputCrossbarSubunits(self, tableIndex, mem):
        return self.switch.inputCrossbarNumSubunits[mem]

    def getAvailableInputCrossbarSubunits(self, tableIndex, mem):
        return self.switch.inputCrossbarNumSubunits[mem] - self.inputCrossbar[mem][self.currentStage]
    
    def getWidthActionData(self, tableIndex):
        return self.preprocess.actionCrossbarNumBits[tableIndex]
        pass

    def getMaximumWidthActionData(self, tableIndex, mem):
        return self.switch.actionCrossbarNumBits

    def getAvailableWidthActionData(self, tableIndex, mem):
        return self.switch.actionCrossbarNumBits -\
            sum([self.actionCrossbar[mem][self.currentStage]\
                     for mem in self.switch.memoryTypes])


    # Advances last block for respective memory by numBlocks
    # (default by number of blocks left in current stage.)
    # At this point, we've checked no constraints will be violated.
    # But validate anyways.
    # Also assigns  mem numBlocks in current stage  to table.
    # And assigns numSubunits of mem input crossbar to table.
    # And assigns widthActionData of mem action crossbar to table.
    def updateLastBlockAndAssign(self, tableIndex, mem, bestFit, numSramBlocksReserved, fill=True):
        numBlocksLeft = self.blocksPerSt[mem] -  (self.lastBlock[mem][self.currentStage] + 1)
        inSram = int(mem == 'sram')
        #numBlocksSram = self.blocksPerSt['sram'] -  (self.lastBlock['sram'][self.currentStage] + 1)

        if fill:
            # If assigning match blocks in SRAM, don't fill up but reserve some SRAM blocks
            self.lastBlock[mem][self.currentStage] += numBlocksLeft - inSram * numSramBlocksReserved
            pass
        else:
            # If assigning match blocks in SRAM, this should leave the reserved
            # blocks untouched, because bestFitForWords['numMatchBlocks'] + ..
            # <= bestFitForBlocks['numMatchBlocks'] + .. which doesn't use
            # reserved SRAM blocks.
            self.lastBlock['sram'][self.currentStage] += bestFit['numActionBlocks']
            self.lastBlock[mem][self.currentStage] += bestFit['numMatchBlocks']
            pass


        index = tableIndex * self.switch.numStages + self.currentStage            
        for thing in ['Action']:
            self.layout[thing.lower()][index, bestFit['pf%s'%thing]] += bestFit['num%sPUnits'%thing]
            self.block[thing.lower()][tableIndex, self.currentStage] += bestFit['num%sBlocks'%thing]
            self.word[thing.lower()][tableIndex, self.currentStage] += bestFit['num%sWords'%thing]
            pass

        self.layout[mem][index, bestFit['pfMatch']] += bestFit['numMatchPUnits']
        self.block[mem][tableIndex, self.currentStage] += bestFit['numMatchBlocks']
        self.word[mem][tableIndex, self.currentStage] += bestFit['numMatchWords']
        self.inputCrossbar[mem][self.currentStage] += self.getInputCrossbarSubunits(tableIndex,mem)
        self.actionCrossbar[mem][self.currentStage] += self.getWidthActionData(tableIndex)
        self.logger.debug("Updated last " + mem + " block to " + str(self.lastBlock[mem][self.currentStage]))

        if (mem != 'sram'):
            self.logger.debug("Updated last SRAM block to " + str(self.lastBlock['sram'][self.currentStage]))
            pass
        
        self.logger.debug("Used " + str(bestFit['numActionBlocks']) + " SRAM blocks for action.")
        self.logger.debug("Used " + str(bestFit['numMatchBlocks']) + " " + mem + " blocks for match.")
        self.logger.debug("Can fit " + str(bestFit['numMatchWords']) + " " + mem + " blocks for match.")
        return

    def getNumSramBlocksReserved(self):
        currentStage = self.currentStage
        table = self.table

        # ternary tables left to assign
        tcamTablesLeft = [table for (table,dist) in self.orderedTables\
                              if table not in self.assigned and\
                              table in self.program.names and\
                              self.program.matchType[\
                self.program.names.index(table)] in ['ternary','lpm'] and\
                              self.getWidthActionData(\
                self.program.names.index(table)) > 0]

        # number of TCAMs left in stage
        numBlocksTcamLeft = self.blocksPerSt['tcam'] - (self.lastBlock['tcam'][currentStage] + 1)
        numBlocksSramLeft = self.blocksPerSt['sram'] - (self.lastBlock['sram'][currentStage] + 1)
                
        # for each table, get PUnit for match TCAM, action
        numActionRamsPerStage = {}
        for table in tcamTablesLeft:
            index = self.program.names.index(table)
            numMatchWordsLeft = self.program.logicalTables[index]
            numMatchPUnitsFromBlocksLeft = int(math.floor(float(numBlocksTcamLeft)/self.blocksPerPf['tcam'][index]))
            numMatchPUnitsFromWordsLeft =  int(math.ceil(float(numMatchWordsLeft)/self.wordsPerPf['tcam'][index]))
            numMatchPUnits = min(numMatchPUnitsFromBlocksLeft, numMatchPUnitsFromWordsLeft)
            numMatchWords = numMatchPUnits * self.wordsPerPf['tcam'][index]
            numActionPUnits = int(math.ceil(float(numMatchWords)/self.wordsPerPf['action'][index]))
            numActionRams = numActionPUnits * self.blocksPerPf['action'][index]
            reserve = min(self.numSramBlocksReserved, numActionRams)
            numActionRamsPerStage[table] = reserve
            pass


        
        if len(tcamTablesLeft) > 0:
            reserveForTables = sorted(tcamTablesLeft, key=lambda t: numActionRamsPerStage[t], reverse=True)
            reserveForTablesStr = ", ".join(["%d for %s" % (numActionRamsPerStage[t], t) for t in reserveForTables])
            self.logger.info("Should reserve %s" %  reserveForTablesStr)
            reserve = numActionRamsPerStage[reserveForTables[0]]
            pass
        else:
            reserve = 0
            self.logger.info("No TCAM tables with action left to be assigned,"+\
                             " reserve 0 SRAMs (table %s, st %d)" % (table, currentStage))
            pass

        return reserve
    
    def solve(self,program, switch, preprocess):
        solveStart = time.time()
        self.program = program
        self.switch = switch
        self.preprocess = preprocess
        self.results = {}
        
        da = RmtDependencyAnalysis(program)
        self.gr = da.getDigraph()
        
        stMax = switch.numStages
        logMax = program.MaximumLogicalTables
        pfMax = {}
        for mem in self.switch.allTypes:
            pfMax[mem] = self.preprocess.layout[mem].shape[1]
            pass

        self.blocksPerSt = {}
        self.numBlocks = {}
        self.blocksPerPf = {}
        self.wordsPerPf = {}
        self.block = {}
        self.layout = {}
        self.word = {} 
        self.inputCrossbar = {}
        self.actionCrossbar = {}
        self.lastBlock = {}

        for mem in self.switch.allTypes:
            self.block[mem] = np.zeros((logMax, stMax))
            self.word[mem] = np.zeros((logMax, stMax))
            self.layout[mem] = np.zeros((logMax * stMax, pfMax[mem]))
            self.blocksPerPf[mem] = self.preprocess.layout[mem]
            self.wordsPerPf[mem]= self.preprocess.word[mem]

            if mem not in self.switch.memoryTypes:
                continue
            self.blocksPerSt[mem] = self.switch.numSlices[mem][0]
            self.numBlocks[mem] = self.blocksPerSt[mem] * stMax
            self.inputCrossbar[mem] = [0] * stMax
            self.actionCrossbar[mem] = [0] * stMax
            self.lastBlock[mem] = [-1] * stMax
            pass

        self.getOrderedTables()
        self.assigned = {}
        self.assigned['start'] = 0
        
        self.results['solved'] = True

        self.currentStage = 0
        self.table = 'begin'
        
        while(self.table != 'end' and self.currentStage < self.switch.numStages):
            self.table, earliest = self.getNextTable()
            if (self.table == 'end'):
                continue
            
            tableIndex = self.getIndex(self.table, program.names)
            self.numWordsLeft = int(program.logicalTables[tableIndex])
                            
            self.logger.info("Next table " + self.table)
            self.logger.debug("number of words left " + str(self.numWordsLeft))

            if self.numWordsLeft == 0:
                self.logger.warn("Next table " + self.table + " is empty!!")
                self.assigned[self.table] = self.currentStage
                continue
            pass

            self.currentStage = earliest 
            mems = self.getMem(tableIndex)
            currentMem = 0
            # Assigns consecutive blocks (skipping stages if needed) to table.

            while(self.numWordsLeft > 0 and self.currentStage < self.switch.numStages):
                lastBlockInCurrentStage = {}
                for mem in self.switch.memoryTypes:
                    lastBlockInCurrentStage[mem] = self.lastBlock[mem][self.currentStage]
                    pass

                self.logger.debug("current table index %d" % tableIndex)
                self.logger.debug("current mem %d" % currentMem)
                self.logger.debug("mems %s" % str(mems))
                numSubunits = self.getInputCrossbarSubunits(tableIndex, mems[currentMem])
                # in RMT, up to 8 input crossbar subunits for each mem, stage
                availableSubunits = self.getAvailableInputCrossbarSubunits(tableIndex, mems[currentMem])
                self.logger.debug("number of input " + mems[currentMem] + " subunits is "\
                                 + str(numSubunits) +\
                                 " and available number of subunits is "\
                                 + str(availableSubunits))
                
                widthActionData = self.getWidthActionData(tableIndex)
                # in RMT, upto 1280 action data bits for both mem, in a stage
                # so we need to store action data usage for all stages at
                # any point in time.
                availableWidthActionData = self.getAvailableWidthActionData(tableIndex, mems[currentMem])
                self.logger.debug("width of action data is "\
                                 + str(widthActionData) +\
                                 " and available action data widths is "\
                                 + str(availableWidthActionData))
                
                # number of table words that can be fit in current stage.
                # numWordsThatCanFit, pfBlocks, pf = self.getBestFitForBlocks(tableIndex, mems[currentMem])

                numSramBlocksReserved = self.getNumSramBlocksReserved()
                
                bestFit = self.getBestFitForBlocks(tableIndex, mems[currentMem], lastBlock=lastBlockInCurrentStage,\
                                                       numSramBlocksReserved=numSramBlocksReserved)
                self.logger.debug("Can fit "\
                                 + str(bestFit['numMatchWords']) + " words in current stage." +\
                                 " and " + str(int(self.numWordsLeft))\
                                 + " words are left.")

                constraintViolatedMsg = ""
                if bestFit['numMatchWords'] == 0:
                    constraintViolatedMsg += "Can't fit any entries (%db). " % self.program.logicalTableWidths[tableIndex]
                    sramsLeft = self.blocksPerSt['sram'] - (self.lastBlock['sram'][self.currentStage] + 1)
                    tcamsLeft = self.blocksPerSt['tcam'] - (self.lastBlock['tcam'][self.currentStage] + 1)
                    if widthActionData > 0:
                        constraintViolatedMsg += "Table has %db action data. " % widthActionData
                        constraintViolatedMsg += "%d RAMs, %d TCAMs left. " % (sramsLeft, tcamsLeft)
                    pass
                if numSubunits > availableSubunits:
                    constraintViolatedMsg += "Need %d %s subunits, only %d available. "\
                        % (numSubunits, mems[currentMem], availableSubunits)
                    pass
                if widthActionData > availableWidthActionData:
                    constraintViolatedMsg += "Need %d action data bits, only %d available. "\
                        % (widthActionData, availableWidthActionData)
                    pass
                if len(constraintViolatedMsg) > 0:
                    constraintViolatedMsg =\
                        "Constraint violated in st %d (%s): %s" % (self.currentStage, mems[currentMem],\
                                                                          constraintViolatedMsg)

                    currentMem = (currentMem + 1)%len(mems)
                    updateMsg = "Moving to %s" % mems[currentMem]
                    if currentMem == 0:
                        self.currentStage += 1
                        updateMsg = "Moving to st %d (%s)." % (self.currentStage, mems[currentMem])
                        pass
                    constraintViolatedMsg += updateMsg
                    self.logger.info(constraintViolatedMsg)

                    pass                
                elif bestFit['numMatchWords'] < self.numWordsLeft:
                    self.logger.debug("assigned remaining blocks in current stage")
                    self.updateLastBlockAndAssign(tableIndex, mems[currentMem], bestFit,\
                                                      numSramBlocksReserved = numSramBlocksReserved,\
                                                      fill=True)
                    
                    self.numWordsLeft -= bestFit['numMatchWords']
                    self.logger.debug(" but " + str(self.numWordsLeft) + " words left.")

                    currentMem = (currentMem + 1)%len(mems)
                    self.logger.debug(" updating current memory type to " + mems[currentMem])
                    if currentMem == 0:
                        self.currentStage += 1
                        self.logger.debug(" updating current stage to " + str(self.currentStage))
                        pass


                    pass

                    pass
                else:
                    bestFit = self.getBestFitForWords(tableIndex, mems[currentMem], lastBlock=lastBlockInCurrentStage, numWordsLeft=self.numWordsLeft)
                    """
                    minBlocksNeeded, pfBlocks, pf, actionBlocks =\
                        bestFit['numMatchBlocks'], bestFit['numMatchPUnits'],\
                        bestFit['pfMatch'], bestFit['numActionBlocks']
                    """
                    self.updateLastBlockAndAssign(tableIndex, mems[currentMem], bestFit,\
                                                      numSramBlocksReserved=numSramBlocksReserved,\
                                                      fill=False)
                    self.assigned[self.table] = self.currentStage
                    self.logger.debug("assigned " + str(bestFit['numMatchBlocks']) + " blocks in current stage")
                    self.logger.debug(" finished with " + str(self.table) +\
                                     " in stage "  + str(self.currentStage))
                    self.numWordsLeft = 0
                    pass
                pass
            if (self.currentStage < self.switch.numStages):            
                string = ""
                for mem in self.switch.memoryTypes:
                    string += "Last %s block " % mem +\
                        str(int(self.lastBlock[mem][self.currentStage]))
                    string += (" is < " + str(int(self.numBlocks[mem] - 1)) + "? ")
                    pass
                
                string += ("Current self.table is " + self.table)
                self.logger.debug(string)
                pass
            elif (self.numWordsLeft > 0):
                numAssigned = len(self.assigned) - ('start' in self.assigned) - ('end' in self.assigned)
                numTables = len(self.program.names)
                self.results['solved'] = False
                self.logger.warn("OUT OF STAGES!!! Could assign " + str(numAssigned) + " tables "\
                                 + " out of " + str(numTables))
                self.logger.warn("No more " + mems[currentMem] + " blocks for " + self.table)
                pass
            pass

        config = RmtConfiguration(program=self.program, switch=self.switch,\
                                      preprocess=self.preprocess,\
                                      layout=self.layout, version=self.version)
        self.logger.info("CONFIGURING LAYOUT FOR %s" % self.layout.keys())

        self.logger.debug("done")
        self.results['power'] = config.getPowerForRamsAndTcams()
        self.results['pipelineLatency'] = config.getPipelineLatency()
        self.results['totalUnassignedWords']= config.totalUnassignedWords
        totalBlocks = np.zeros((stMax))
        for st in range(stMax):
            totalBlocks[st] = sum([self.block[mem][log,st] for\
                                       mem in self.switch.memoryTypes for\
                                       log in range(logMax)])
            pass
        self.results['numStages'] = max([st for st in range(stMax) if\
                                                   totalBlocks[st] > 0])+1

        solveEnd = time.time()
        self.results['solveTime'] = solveEnd - solveStart
        
        configs = {}
        configs['greedyConfig'] = config

        return configs
