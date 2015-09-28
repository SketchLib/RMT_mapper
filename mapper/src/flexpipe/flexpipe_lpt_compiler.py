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



from flexpipe_configuration import FlexpipeConfiguration
import numpy as np

import math
import operator
import parser
#import pydot
import sys
import logging
import copy
from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph
from pygraph.algorithms.minmax import shortest_path
#from pygraph.readwrite.dot import write

class FlexpipeLptCompiler:
    """ Greedy heuristic compiler for FlexPipe target, 
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        pass

    def getIndex(self, table, names):
        i = 0
        for name in names:
            if table == name:
                return i
            i += 1
            pass
        self.logger.warn(str(table) + " not found in names.")
        return len(names)
    

    def getBlocksInStage(self, mem, st):
        """ Returns indices of memory blocks of type @mem in stage @st
        Indexing starts at 0 and covers all blocks of every memory
        type in every stage.
        """
        
        startBlock = 0
        for stage in range(0,st):
            startBlock += self.switch.numBlocks[mem][stage]
            pass
        
        return range(startBlock, startBlock + self.switch.numBlocks[mem][st])
    
    def getNextTable(self):
        """  Get the next table from the heuristic order that hasn't been
        assigned yet.
        """

        succWeight = 0
#        self.logger.debug("Looking for next table")
        for table in self.orderedTables:
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
                    return table, max(earliestStage)
                pass
            pass
        self.logger.debug("No table left that can be assigned.")
        return None

    def getMem(self, tableIndex):
        """ Returns valid memory types for given table"""
        validMems = []
        for mem in self.preprocess.use:
            if self.preprocess.use[mem][tableIndex] == 1\
                    and mem in self.switch.numBlocks:
                validMems.append(mem)
                pass
            pass
        return validMems

    def makeGraph(self, program):
        """ Sets up dependency graph, only match edges force
        a table to a new stage, so are weighted 1,
        others are weighted 0.
        Used to order tables in setupNextTable().
        """
        gr = digraph()
        gr.add_nodes(program.names)

        gr.add_nodes(['start','end'])

                     
        for pair in program.logicalSuccessorDependencyList:
            log1 = program.names[pair[0]]
            log2 = program.names[pair[1]]
            self.logger.debug("adding successor edge " + log1 + " -> " + log2)
            gr.add_edge((log2,log1),0)
            pass

        for pair in program.logicalMatchDependencyList:
            log1 = program.names[pair[0]]
            log2 = program.names[pair[1]]
            self.logger.debug("adding match edge " + log1 + " -> " + log2)
            gr.add_edge((log2,log1),-1)

            pass

        for pair in program.logicalActionDependencyList:
            log1 = program.names[pair[0]]
            log2 = program.names[pair[1]]
            self.logger.debug("adding action edge " + log1 + " -> " + log2)
            gr.add_edge((log2,log1),0)
            pass

        for log in program.names:
            if gr.neighbors(log) == []:
                gr.add_edge((log, 'start'),0)
                self.logger.debug("adding edge " + " start " + " -> " + log )
                pass
            if gr.incidents(log) == []:
                gr.add_edge(('end',log),0)
                self.logger.debug("adding edge " + log + " -> " + " end ")
                pass
            pass
        self.gr = gr
        pass

    def getMemTypesInStage(self):
        """ Get memory types in self.currentStage """
        memTypes = []
        for st, mem in self.memPerStage:
            if st == self.currentStage:
                memTypes.append(mem)
                pass
            pass
        return memTypes
    
    def setupSwitchToNext(self):
        """ Order available (st, mem) tuples, so we can iterate
        through self.memPerStage using switchToNext()
        when assigning tables
        """
        self.memPerStage = []
        for st in range(self.switch.numStages):
            for mem in self.switch.memoryTypes:
                if self.switch.numBlocks[mem][st] > 0:
                    self.memPerStage.append((st, mem))
                    pass
                pass
            pass
        self.logger.debug("Valid memories per stage")
        self.logger.debug(self.memPerStage)
        pass
    
    def setupTablesInBlock(self):
        """" Setup self.tablesInBlock[mem][sl] which 
        will contain names of all the tables assigned
        to the sl-th block of type mem (index sl starts
        at 0 and covers all blocks of type mem in
        across all stages)
        Filled in and used while assigning tables.
        """
                
        self.tablesInBlock = {}


        for mem in self.switch.memoryTypes:
            self.tablesInBlock[mem] = {}
            for sl in range(sum(self.switch.numBlocks[mem])):
                self.tablesInBlock[mem][sl] = {}
                pass
            pass

        # TODO(lav): Useless code?
        memIndex = 0
        mem = self.switch.memoryTypes[memIndex]
        blocks = self.getBlocksInStage(mem, 0)
        while len(blocks) == 0:
            memIndex += 1
            mem = self.switch.memoryTypes[memIndex]
            blocks = self.getBlocksInStage(mem, 0)
            pass
        pass

    def setupDirty(self):
        """ self.dirty[mem][row,sl] indicates if @row in the
        @sl-th @mem block has been assigned to some table.
        Filled in and used while assigning tables.
        """
        self.dirty = {}
        for mem in self.switch.memoryTypes:
            shape = (self.switch.depth[mem], sum(self.switch.numBlocks[mem]))
            self.dirty[mem] = np.zeros(shape)
            pass
        pass

    def setupAssigned(self):
        """ Maps table name to last stage it was assigned to. """
        self.assigned = {}
        self.assigned['start'] = 0
        pass

    def setupLastBlock(self):
        """ sets up self.lastBlockOfRow[mem][st][row]
        which is the last block in @mem, @st where
        @row has been assigned to some table. Initial
        value is -1.
        also sets up self.lastBlockOf[mem][st][tableIndex]
        which is the last block in @mem, @st that has been
        assigned to @tableIndex.
        Filled in and used while assigning tables.
        """
        self.lastBlockOfRow = {}
        self.lastBlockOfTable = {}
        for mem in self.switch.memoryTypes:
            self.lastBlockOfRow[mem] = {}
            self.lastBlockOfTable[mem] = {}
            for st in range(self.switch.numStages):
                # last block is actually one more than last block used
                self.lastBlockOfRow[mem][st] = [-1] * self.switch.depth[mem]
                self.lastBlockOfTable[mem][st] = [-1] * self.program.MaximumLogicalTables
                pass
            pass
        pass

    def setupRowsPerBlock(self):
        """
        Sets up the following containers
        startRowDict[mem][log,sl] which is @row if the table
        @log starts in @row of the @sl-th @mem memory block,
        and zero otherwise.
        
        numberOfRows[mem][log,sl] = num which is the number
        of rows of table in the @sl-th @mem memory block
        (when the table's match entries start in the block).
        If there are no match entries in a block, or if
        a match entry starts in a previous block but only
        spills into this block @sl, then @num is 0.

        """
        self.startRowDict = {}
        self.numberOfRowsDict = {}
        for mem in self.switch.memoryTypes:
            shape = (self.program.MaximumLogicalTables, sum(self.switch.numBlocks[mem]))
            self.startRowDict[mem] = np.zeros(shape)
            self.numberOfRowsDict[mem] = np.zeros(shape)
            pass
        pass

    def setupNextTable(self):
        """
        Orders tables in order of "most constrained first"
        (MCF) where a table is more constrained if it can go in
        only a few @possible_stages based on 
        - its level (maxmimum distance from end of program in
        the dependency chain)
        - memory types it can go into
        Ties are broken in favor of wider tables first.
        """
        stEnd, distFromEnd = shortest_path(self.gr, 'end')
        tables = [k for k in distFromEnd.keys() if k not in ['end','start']]
        width = {}
        mems = {}

        for t in sorted(tables, key=lambda t: distFromEnd[t]):
            index = self.getIndex(t,self.program.names)
            width[t] = self.program.logicalTableWidths[index]
            mems[t] = self.getMem(index)
            self.logger.debug("Table %s,\n" % t +\
                             "max. dist. from end: %d" % abs(distFromEnd[t]) +\
                             ", valid memory types: %s" % str(mems[t]))
            pass

        possible_stages = {}
        
        for t in tables:
            possible_stages[t] = [st for st in range(self.switch.numStages)\
                                      if st < self.switch.numStages - abs(distFromEnd[t]) and\
                                      any([m for m in mems[t] if (st,m) in self.memPerStage])]
            pass

        for t in sorted(possible_stages.keys(), key=lambda t: len(possible_stages[t])):
            self.logger.debug("Table %s can go in stages %s" % (t, possible_stages[t]))
            pass
                
        tables.append('start')
        width['start'] = 0
        mems['start'] = []
        possible_stages['start'] = [0]
        tables.append('end') 
        width['end'] = 0
        mems['end'] = []
        possible_stages['end'] = range(self.switch.numStages)

        widths = [(t, width[t]) for t in tables]
        widths = sorted(widths, key = lambda pair: pair[1], reverse=True)

        self.logger.info("Table in most constrained first order"\
                             + " (i.e., ordered by number of stages table can go in"\
                             + " based on its level and match type, ties broken by match width)")
                         
        self.logger.info('%25s%20s%4s%30s%4s' % ('tablename',  'Stages', 'Level', 'Mems', 'M-W'))

        sortby = sorted(tables, key = lambda t: (len(possible_stages[t]),-width[t]))
        for t in sortby:
            if (t in ['start','end']):
                continue
            ostr = '%25s%20s%4d%30s%4d' %\
                (str(t),\
                      str(possible_stages[t]),\
                      abs(distFromEnd[t]),\
                      str([mem[:4] for mem in mems[t]]),\
                     width[t])
            self.logger.info(ostr)
            pass

        self.orderedTables = sortby

        pass

    def getNextRange(self):
        """ Returns the next chunk of free consecutive blocks/ rows we can use to assign
        current self.table in self.currentStage.
        """
        mem = self.mems[self.currentMem]
        st = self.currentStage
        table = self.table
        tableIndex = self.tableIndex
        
        blocksInStage = self.getBlocksInStage(mem, st)
        blocksNeeded = int(self.preprocess.pfBlocks[mem][tableIndex])
        
        def slRange(r):
            """ Returns range of blocks that current table would
            occupy if it starts in row @r of the earliest possible
            block in the current stage.
            """
            start = max([self.lastBlockOfRow[mem][st][r],\
                             self.lastBlockOfTable[mem][st][tableIndex]])
            # Last block of row not updated yet,
            # so start from first block of stage
            if (start == -1):
                if len(blocksInStage) == 0:
                    return []
                start = blocksInStage[0]
                pass
            else:
                start += 1
                pass

            end = start + blocksNeeded
            if end > blocksInStage[-1]:
                end = blocksInStage[-1]+1
                pass

            return range(start, end)
        # rows where we have enough consecutive blocks for
        # at least one match entry (width), and where for each
        # block, no other table starts in the same row
        # and we don't exceed the max. tables allowed per block.
        validRows = [r for r in range(self.switch.depth[mem]) if\
                         len(slRange(r)) >= blocksNeeded and\
                         not any([self.dirty[mem][r,sl]==1 or\
                                      len(self.tablesInBlock[mem][sl]) > \
                                      self.switch.maxTablesPerBlock-1 \
                                      for sl in slRange(r)])]
                     
        if len(validRows) > 0:
            # startRow is the row with the earliest possible last assigned block
            # so we can start table in the top-left most row/block possible
            startRow = min(validRows, key = lambda r: self.lastBlockOfRow[mem][st][r])
            startBlock = max(self.lastBlockOfTable[mem][st][tableIndex],\
                                 self.lastBlockOfRow[mem][st][startRow])
            if (startBlock == -1):
                startBlock = blocksInStage[0]
                pass
            else:
                startBlock += 1
                pass

            newSlRange = range(startBlock, startBlock + blocksNeeded)

            # only pick those valid rows that start from startRow
            # and for which startBlock .. startBlock + blocksNeeded
            # is free to use
            newValidRows = [r for r in validRows if\
                                r >= startRow and\
                                not any([self.dirty[mem][r,sl]==1 or\
                                             len(self.tablesInBlock[mem][sl]) > \
                                             self.switch.maxTablesPerBlock-1 \
                                             for sl in newSlRange])]
            numRows = 1
            # Of the new valid rows, use the largest number of
            # consecutive rows starting at @startRow.
            for i in range(1, len(newValidRows)):
                if newValidRows[i] > newValidRows[i-1] + 1:
                    break
                numRows += 1
                pass
            rowRange = range(startRow, startRow+numRows)
            wordsLeft = int(self.numWordsLeft)
            if wordsLeft < len(rowRange):
                rowRange = rowRange[0:wordsLeft]
                pass

            #self.logger.debug("Row range: " + str(rowRange[0]) + ", " + str(rowRange[-1]))
            #self.logger.debug("Block range: " + str(newSlRange[0]) + ", " + str(newSlRange[-1]))

            return newSlRange, rowRange

        return [], []

    def assignRowsToTable(self):
        """
        Assign self.slRange and self.rowRange (chunk of consecutive blocks/ rows)
        to current table self.tableIndex. Here, we basically update the different
        data structures that track which table is assigned to which row/ block
        i.e., self.startRowDict[mem][t,sl], self.tablesInBlock[mem][sl][table]
        self.lastBlockOfRow[mem][st][r], self.numberOfRowsDict[mem][t,sl]
        self.dirty[mem][r,sl], self.lastBlockOfTable[mem][st][t], all of
        these are initialized in the various setup... functions.
        """
        st = self.currentStage
        mem = self.mems[self.currentMem]
        tableIndex = self.tableIndex
        self.startRowDict[mem][tableIndex,self.slRange[0]] = self.rowRange[0]
        for sl in self.slRange:
            self.tablesInBlock[mem][sl][self.table] = 1
            pass
        for r in self.rowRange:
            self.lastBlockOfRow[mem][st][r] = self.slRange[-1]
            self.numberOfRowsDict[mem][tableIndex,self.slRange[0]] += 1
            for sl in self.slRange:
                self.dirty[mem][r,sl] = 1
                pass
            self.numWordsLeft -= 1
            pass
        self.logger.debug("Assigned " + str(len(self.rowRange)) + " rows from "\
                     + str(self.rowRange[0]) + " to " + str(self.rowRange[-1]) +\
                     "in blocks " + str(self.slRange[0]) + " to " + str(self.slRange[-1])\
                     + " of " + mem)
        self.lastBlockOfTable[mem][st][tableIndex] = self.slRange[-1]
        pass

    def switchToNextStage(self):
        """ Update current stage/ memory type to next st, mem, where mem is a
        valid memory type of the current table
        """
        if self.currentMem == -1:
            index = self.getIndex(self.currentStage, [st for (st,mem) in self.memPerStage]) - 1
            pass
        else:
            index = self.getIndex((self.currentStage,self.mems[self.currentMem]), self.memPerStage)
            pass
        
        for (st,mem) in self.memPerStage[index+1:]:
            if mem in self.mems:
                if st != self.currentStage:
                    self.logger.debug(" updating current stage to " + str(st))
                    pass
                self.currentStage = st
                self.currentMem = self.getIndex(mem, self.mems)
                self.logger.debug(" updating current memory type to " + self.mems[self.currentMem])
                return
            pass

        # couldn't find a next stage
        self.currentStage = self.switch.numStages
        self.logger.warn("couldn't find a mem for " + self.table + " in remaining stages" +\
                     " updating current stage to " + str(self.currentStage)+\
                     " and current memory (irrelevant, doesn't work for "\
                     + self.table + "): " + self.memPerStage[self.currentMem][1])
        return
        pass

    def logCompilerAttempt(self, compilerAttempt):
        if 'solved' not in compilerAttempt:
            return
        if (compilerAttempt['solved']):
            self.logger.info("Compiler attempt successful.")
            pass
        else:
            self.logger.info("Compiler attempt unsuccessful.")
            if 'tables' in compilerAttempt and len(compilerAttempt['tables']) > 0:
                lastTable = compilerAttempt['tables'][-1]
                self.logger.info("Failed to assign last table " + lastTable)
                pass
            pass
            
        if (not ('tables' in compilerAttempt and len(compilerAttempt['tables']) > 0)):
            return

        self.logger.info(
            "Attempted to assign the following tables in order: "
            + str(compilerAttempt['tables']))
        self.logger.info("Format: table in start_stage .. end_stage: stage mem: words_assigned; ..")
        self.logger.info("words_assigned is X when no words were assigned because there was no free row for a match entry")
        for table in compilerAttempt['tables']:
            if table not in compilerAttempt['tableInfo']:
                continue
            tableInfo = compilerAttempt['tableInfo'][table]
            tableInfoStr = "Table %s " % (table)
            constraintViolatedStr = ""
            if len(tableInfo) == 0:
                continue
            stages = sorted(tableInfo.keys())
            if (len(stages) == 0):
                continue
            tableInfoStr += "in %d .. %d: " % (stages[0], stages[-1])
            for st in stages:
                mems = sorted(tableInfo[st].keys())
                for mem in mems:
                    memInfo = tableInfo[st][mem]
                    words = 0
                    if 'numWordsAssigned' in memInfo:
                        words = memInfo['numWordsAssigned']
                        pass
                    if  words > 0:
                        tableInfoStr += " St %d %s: %d" % (st, mem, words)
                        pass
                    else:
                        tableInfoStr += " St %d %s: X" % (st, mem)
                        pass
                    if mem == mems[-1]:
                        tableInfoStr += "; "
                        pass
                    pass # ends for mem in mems
                pass # ends for st in stages
            self.logger.info(tableInfoStr);
            pass # ends for table in compilerAttempt['tables']        
    pass

    def solve(self, program, switch, preprocess):
        """ Runs the MCF greedy heuristic and returns switch configuration"""

        self.program = program
        self.switch = switch
        self.preprocess = preprocess
        self.results = {}
        
        self.makeGraph(program)

        # Order all possible stage, mem so we can iterate through them easily
        self.setupSwitchToNext()
        # Order tables according to MCF metric so we can iterate with getNextTable()
        self.setupNextTable()

        # Set up different data structures to keep track of table assignment
        self.setupTablesInBlock()
        self.setupDirty() # dirty[mem][row,sl] = 0 or 1
        self.setupAssigned() # assigned[table] = st
        # lastBlockOfRow[mem][st][row] = sl, lastBlockOfTable[mem][st][log] = sl
        self.setupLastBlock()
        # startRowDict[mem][log,sl] = row, numberOfRows[mem][log,sl] = num
        self.setupRowsPerBlock()
        self.assigned['start'] = 0

        # variables that track current stage, table
        self.currentStage = 0
        self.table = 'start'        
        self.tableIndex = -1
        # valid memory types for current table
        self.mems = []
        # number of match entries left to assign
        self.numWordsLeft = 0
        
        self.results['solved'] = True

        # While compiler simply gives up when a program doesn't fit
        # We can output some helpful information from the compilation attempt
        # so the user can figure out how to modify the program
        # order of tables attempted, table that didn't fit
        # for each table, number of match entries fit in each stage
        # we'll store all this info. in @compilerAttempt
        compilerAttempt = {}
        compilerAttempt['solved'] = True
        compilerAttempt['tables'] = []
        compilerAttempt['tableInfo'] = {}

        # the greedy heuristic assignment process
        # the outer loop iterates through tables (already ordered by
        #  "most constrained first")
        # the inner loop iterates through chunks of
        #  consecutive rows/ blocks ("range")
        # that a table can be assigned to all the way until the all
        # entries of the table are assigned (or it runs out of stages)
        nextTables = ""
        while self.table != 'end' and\
                self.currentStage < self.switch.numStages:
            self.table, earliest = self.getNextTable()
            compilerAttempt['tables'].append(self.table)
            compilerAttempt['tableInfo'][self.table] = {}

            if (self.table == 'end'):
                continue
            self.tableIndex = self.getIndex(self.table, self.program.names)
            self.numWordsLeft = self.program.logicalTables[self.tableIndex]
            if self.numWordsLeft == 0:
                self.logger.warn("Next table " + self.table + " is empty!!")
                self.assigned[self.table] = self.currentStage
                continue                

            self.currentStage = earliest
            self.mems = self.getMem(self.tableIndex)
            self.currentMem = -1
            # to get to right memory type
            self.switchToNextStage()
            
            compilerAttempt['tableInfo'][self.table][self.currentStage] = {}
            compilerAttempt['tableInfo'][self.table][self.currentStage]\
            [self.mems[self.currentMem]] = {}
            compilerAttempt['tableInfo'][self.table][self.currentStage]\
            [self.mems[self.currentMem]]['numWordsAssigned'] = 0
            compilerAttempt['tableInfo'][self.table][self.currentStage]\
            [self.mems[self.currentMem]]['numWordsLeft'] = self.numWordsLeft

            # Possible that table can't use this mem, handle later            
            blocksNeeded = int(self.preprocess.pfBlocks[self.mems[self.currentMem]]\
                                                            [self.tableIndex])

            nextTables += "%s (%d), " % (self.table, earliest)
            self.logger.debug("Next table " + self.table + ", # words " + str(self.numWordsLeft) +\
                         ", # blocks " + str(blocksNeeded) + ", earliest stage " +\
                         str(earliest))
                
            # Assigns ranges (consecutive rows in consecutive blocks)
            #  (skipping stages if needed) to table.
            while self.numWordsLeft > 0 and self.currentStage < self.switch.numStages:
                self.slRange, self.rowRange = self.getNextRange()
                if any ([len(self.slRange)==0, len(self.rowRange)==0]):
                    self.logger.debug("next range is empty, switchToNextstage()")

                    if (compilerAttempt['tableInfo'][self.table][self.currentStage]
                        [self.mems[self.currentMem]]['numWordsAssigned'] == 0):
                        compilerAttempt['tableInfo'][self.table][self.currentStage]\
                        [self.mems[self.currentMem]]['constraintViolatedMsg'] =\
                        "No " + str(blocksNeeded) + "-block wide ranges available for table"
                        pass
                    
                    self.switchToNextStage()                   

                    if (self.currentStage not in  compilerAttempt['tableInfo'][self.table]):
                        compilerAttempt['tableInfo'][self.table][self.currentStage] = {}
                        pass
                    if (self.mems[self.currentMem] not in  compilerAttempt['tableInfo'][self.table]):                    
                        compilerAttempt['tableInfo'][self.table][self.currentStage]\
                        [self.mems[self.currentMem]] = {}
                        compilerAttempt['tableInfo'][self.table][self.currentStage]\
                        [self.mems[self.currentMem]]['numWordsAssigned'] = 0
                        compilerAttempt['tableInfo'][self.table][self.currentStage]\
                        [self.mems[self.currentMem]]['numWordsLeft'] = self.numWordsLeft
                        pass
                    continue
                else:
                    self.logger.debug("assigning rows to table")
                    oldNumWordsLeft = copy.copy(self.numWordsLeft)
                    self.assignRowsToTable()
                    newNumWordsLeft = copy.copy(self.numWordsLeft)
                    if (newNumWordsLeft < oldNumWordsLeft):
                        compilerAttempt['tableInfo'][self.table][self.currentStage]\
                        [self.mems[self.currentMem]]['numWordsAssigned']\
                        += oldNumWordsLeft - newNumWordsLeft
                        pass
                    pass
                pass
            
            if (self.numWordsLeft == 0 and self.currentStage < self.switch.numStages):
                self.logger.debug("Finished " + self.table)
                self.assigned[self.table] = self.currentStage
                pass

            if (self.numWordsLeft > 0):
                compilerAttempt['solved'] = False
                self.results['solved'] = False
                self.logger.warn("No more memory for " + self.table)
                pass
            pass

        if self.table == 'end':
            self.assigned['end'] = -1
            pass
        
        numAssigned = len(self.assigned)
        numTables = len(self.program.names) 
        
        
        self.logger.debug(str(numAssigned) + " out of " + str(numTables+2))
        self.logger.debug("Tables assigned in order (tableName, earliestSt)- %s " %\
                        nextTables)
        if 'start' in self.assigned:
            numAssigned -= 1
            pass
        if 'end' in self.assigned:
            numAssigned -= 1
            pass
        self.numAssigned = numAssigned
        self.numTables = numTables

        self.logCompilerAttempt(compilerAttempt)
        config = FlexpipeConfiguration(program=self.program, switch=self.switch,\
                                      preprocess=self.preprocess, version="Greedy")
        config.configure(self.startRowDict, self.numberOfRowsDict)
        self.logger.debug("done")

        for mem in self.switch.memoryTypes:
            order = 0
            
            self.results['usedBlocks'+mem] =\
                int(sum([1 for sl in range(sum(self.switch.numBlocks[mem])) if\
                             any([round(self.numberOfRowsDict[mem][log, sl]) > 0\
                                     for log in range(self.numTables)])]))
            pass

        self.results['totalUsedBlocks'] =\
            sum([self.results['usedBlocks'+mem]\
                     for mem in self.switch.memoryTypes])

        configs = {}
        configs['greedyConfig'] = config
        return configs
