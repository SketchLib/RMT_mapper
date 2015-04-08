from flexpipe_configuration import FlexpipeConfiguration
import numpy as np

import math
import operator
import parser
#import pydot
import sys
import logging
from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph
from pygraph.algorithms.minmax import shortest_path
#from pygraph.readwrite.dot import write

class FlexpipeLptCompiler:
    def __init__(self):
        pass

    def getIndex(self, table, names):
        i = 0
        for name in names:
            if table == name:
                return i
            i += 1
            pass
        logging.warn(str(table) + " not found in names.")
        return len(names)
    

    def getSlicesInStage(self, mem, st):
        startSlice = 0
        for stage in range(0,st):
            startSlice += self.switch.numSlices[mem][stage]
            pass
        
        return range(startSlice, startSlice + self.switch.numSlices[mem][st])
    
    def getNextTable(self):
        succWeight = 0
#        logging.debug("Looking for next table")
        for table in self.orderedTables:
            if table not in self.assigned:
                logging.debug("Table " + table + "?")
                previousTables = self.gr.neighbors(table)
                logging.debug("Must assign " + str(previousTables) + " first")
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
        logging.debug("No table left that can be assigned.")
        return None

    def getMem(self, tableIndex):
        validMems = []
        for mem in self.preprocess.use:
            if self.preprocess.use[mem][tableIndex] == 1\
                    and mem in self.switch.numSlices:
                validMems.append(mem)
                pass
            pass
        return validMems

    def makeGraph(self, program):
        gr = digraph()
        gr.add_nodes(program.names)

        gr.add_nodes(['start','end'])

                     
        for pair in program.logicalSuccessorDependencyList:
            log1 = program.names[pair[0]]
            log2 = program.names[pair[1]]
            logging.debug("adding successor edge " + log1 + " -> " + log2)
            gr.add_edge((log2,log1),0)
            pass

        for pair in program.logicalMatchDependencyList:
            log1 = program.names[pair[0]]
            log2 = program.names[pair[1]]
            logging.debug("adding match edge " + log1 + " -> " + log2)
            gr.add_edge((log2,log1),-1)

            pass

        for pair in program.logicalActionDependencyList:
            log1 = program.names[pair[0]]
            log2 = program.names[pair[1]]
            logging.debug("adding action edge " + log1 + " -> " + log2)
            gr.add_edge((log2,log1),0)
            pass

        for log in program.names:
            if gr.neighbors(log) == []:
                gr.add_edge((log, 'start'),0)
                logging.debug("adding edge " + " start " + " -> " + log )
                pass
            if gr.incidents(log) == []:
                gr.add_edge(('end',log),0)
                logging.debug("adding edge " + log + " -> " + " end ")
                pass
            pass
        self.gr = gr
        pass

    def getMemTypesInStage(self):
        memTypes = []
        for st, mem in self.memPerStage:
            if st == self.currentStage:
                memTypes.append(mem)
                pass
            pass
        return memTypes
    
    def setupSwitchToNext(self):
        self.memPerStage = []
        for st in range(self.switch.numStages):
            for mem in self.switch.memoryTypes:
                if self.switch.numSlices[mem][st] > 0:
                    self.memPerStage.append((st, mem))
                    pass
                pass
            pass
        logging.debug("Valid memories per stage")
        logging.debug(self.memPerStage)
        pass
    
    def setupTablesInSlice(self):
        self.tablesInSlice = {}


        for mem in self.switch.memoryTypes:
            self.tablesInSlice[mem] = {}
            for sl in range(sum(self.switch.numSlices[mem])):
                self.tablesInSlice[mem][sl] = {}
                pass
            pass

        memIndex = 0
        mem = self.switch.memoryTypes[memIndex]
        slices = self.getSlicesInStage(mem, 0)
        while len(slices) == 0:
            memIndex += 1
            mem = self.switch.memoryTypes[memIndex]
            slices = self.getSlicesInStage(mem, 0)
            pass
        pass

    def setupDirty(self):
        self.dirty = {}
        for mem in self.switch.memoryTypes:
            shape = (self.switch.depth[mem], sum(self.switch.numSlices[mem]))
            self.dirty[mem] = np.zeros(shape)
            pass
        pass

    def setupAssigned(self):            
        self.assigned = {}
        self.assigned['start'] = 0
        pass

    def setupLastSlice(self):    
        self.lastSliceOfRow = {}
        self.lastSliceOfTable = {}
        for mem in self.switch.memoryTypes:
            self.lastSliceOfRow[mem] = {}
            self.lastSliceOfTable[mem] = {}
            for st in range(self.switch.numStages):
                # last slice is actually one more than last slice used
                self.lastSliceOfRow[mem][st] = [-1] * self.switch.depth[mem]
                self.lastSliceOfTable[mem][st] = [-1] * self.program.MaximumLogicalTables
                pass
            pass
        pass

    def setupRowsPerSlice(self):
        self.startRowDict = {}
        self.numberOfRowsDict = {}
        for mem in self.switch.memoryTypes:
            shape = (self.program.MaximumLogicalTables, sum(self.switch.numSlices[mem]))
            self.startRowDict[mem] = np.zeros(shape)
            self.numberOfRowsDict[mem] = np.zeros(shape)
            pass
        pass

    def setupNextTable(self):
        stEnd, distFromEnd = shortest_path(self.gr, 'end')
        tables = [k for k in distFromEnd.keys() if k not in ['end','start']]
        width = {}
        mems = {}

        for t in sorted(tables, key=lambda t: distFromEnd[t]):
            index = self.getIndex(t,self.program.names)
            width[t] = self.program.logicalTableWidths[index]
            mems[t] = self.getMem(index)
            logging.info("Table %s,\n" % t +\
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
            logging.info("Table %s can go in stages %s" % (t, possible_stages[t]))
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


        sortby = sorted(tables, key = lambda t: (len(possible_stages[t]),-width[t]))
        for t in sortby:
            logging.info("Table %s can go in stages %s, has width %d" % (t, possible_stages[t], width[t]))
            pass

        self.orderedTables = sortby

        pass

    def getNextRange(self):

        mem = self.mems[self.currentMem]
        st = self.currentStage
        table = self.table
        tableIndex = self.tableIndex
        
        slicesInStage = self.getSlicesInStage(mem, st)
        slicesNeeded = int(self.preprocess.pfBlocks[mem][tableIndex])
        
        def slRange(r):
            start = max([self.lastSliceOfRow[mem][st][r],\
                             self.lastSliceOfTable[mem][st][tableIndex]])
            # Last slice of row not updated yet,
            # so start from first slice of stage
            if (start == -1):
                if len(slicesInStage) == 0:
                    return []
                start = slicesInStage[0]
                pass
            else:
                start += 1
                pass

            end = start + slicesNeeded
            if end > slicesInStage[-1]:
                end = slicesInStage[-1]+1
                pass

            return range(start, end)

        validRows = [r for r in range(self.switch.depth[mem]) if\
                         len(slRange(r)) >= slicesNeeded and\
                         not any([self.dirty[mem][r,sl]==1 or\
                                      len(self.tablesInSlice[mem][sl]) > \
                                      self.switch.maxTablesPerSlice-1 \
                                      for sl in slRange(r)])]
                     
        if len(validRows) > 0:
            startRow = min(validRows, key = lambda r: self.lastSliceOfRow[mem][st][r])
            startSlice = max(self.lastSliceOfTable[mem][st][tableIndex],\
                                 self.lastSliceOfRow[mem][st][startRow])
            if (startSlice == -1):
                startSlice = slicesInStage[0]
                pass
            else:
                startSlice += 1
                pass

            newSlRange = range(startSlice, startSlice + slicesNeeded)

            
            newValidRows = [r for r in validRows if\
                                r >= startRow and\
                                not any([self.dirty[mem][r,sl]==1 or\
                                             len(self.tablesInSlice[mem][sl]) > \
                                             self.switch.maxTablesPerSlice-1 \
                                             for sl in newSlRange])]
            numRows = 1
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

            #logging.debug("Row range: " + str(rowRange[0]) + ", " + str(rowRange[-1]))
            #logging.debug("Slice range: " + str(newSlRange[0]) + ", " + str(newSlRange[-1]))

            return newSlRange, rowRange

        return [], []

    def assignRowsToTable(self):
        st = self.currentStage
        mem = self.mems[self.currentMem]
        tableIndex = self.tableIndex
        self.startRowDict[mem][tableIndex,self.slRange[0]] = self.rowRange[0]
        for sl in self.slRange:
            self.tablesInSlice[mem][sl][self.table] = 1
            pass
        for r in self.rowRange:
            self.lastSliceOfRow[mem][st][r] = self.slRange[-1]
            self.numberOfRowsDict[mem][tableIndex,self.slRange[0]] += 1
            for sl in self.slRange:
                self.dirty[mem][r,sl] = 1
                pass
            self.numWordsLeft -= 1
            pass
        logging.debug("Assigned " + str(len(self.rowRange)) + " rows from "\
                     + str(self.rowRange[0]) + " to " + str(self.rowRange[-1]) +\
                     "in slices " + str(self.slRange[0]) + " to " + str(self.slRange[-1])\
                     + " of " + mem)
        self.lastSliceOfTable[mem][st][tableIndex] = self.slRange[-1]
        pass

    def switchToNextStage(self):
        if self.currentMem == -1:
            index = self.getIndex(self.currentStage, [st for (st,mem) in self.memPerStage]) - 1
            pass
        else:
            index = self.getIndex((self.currentStage,self.mems[self.currentMem]), self.memPerStage)
            pass
        
        for (st,mem) in self.memPerStage[index+1:]:
            if mem in self.mems:
                if st != self.currentStage:
                    logging.debug(" updating current stage to " + str(st))
                    pass
                self.currentStage = st
                self.currentMem = self.getIndex(mem, self.mems)
                logging.debug(" updating current memory type to " + self.mems[self.currentMem])
                return
            pass

        # couldn't find a next stage
        self.currentStage = self.switch.numStages
        logging.warn("couldn't find a mem for " + self.table + " in remaining stages" +\
                     " updating current stage to " + str(self.currentStage)+\
                     " and current memory (irrelevant, doesn't work for "\
                     + self.table + "): " + self.memPerStage[self.currentMem][1])
        return
        pass

    def solve(self, program, switch, preprocess):
        self.program = program
        self.switch = switch
        self.preprocess = preprocess
        self.results = {}
        
        self.makeGraph(program)


        self.setupSwitchToNext() # sorts st, mem by increasing stage for switchToNext()
        self.setupNextTable() # sorts table by decreasing widths for getNextTable()

        self.setupTablesInSlice() # tablesInSlice[mem][sl] = {}
        self.setupDirty() # dirty[mem][row,sl] = 0 or 1
        self.setupAssigned() # assigned[table] = st

        # lastSliceOfRow[mem][st][row] = sl, lastSliceOfTable[mem][st][log] = sl
        self.setupLastSlice()

        # startRowDict[mem][log,sl] = row, numberOfRows[mem][log,sl] = num
        self.setupRowsPerSlice()

        self.currentStage = 0
        self.table = 'start'        
        self.mems = []
        self.numWordsLeft = 0
        self.tableIndex = -1
        self.assigned['start'] = 0
        self.results['solved'] = True
        nextTables = ""
        while self.table != 'end' and\
                self.currentStage < self.switch.numStages:
            self.table, earliest = self.getNextTable()
            if (self.table == 'end'):
                continue
            self.tableIndex = self.getIndex(self.table, self.program.names)
            self.numWordsLeft = self.program.logicalTables[self.tableIndex]
            if self.numWordsLeft == 0:
                logging.warn("Next table " + self.table + " is empty!!")
                self.assigned[self.table] = self.currentStage
                continue                

            self.currentStage = earliest
            self.mems = self.getMem(self.tableIndex)
            self.currentMem = -1
            # to get to right memory type
            self.switchToNextStage()
            
            # Possible that table can't use this mem, handle later
            
            slicesNeeded = int(self.preprocess.pfBlocks[self.mems[self.currentMem]]\
                                                            [self.tableIndex])

            nextTables += "%s (%d), " % (self.table, earliest)
            logging.debug("Next table " + self.table + ", # words " + str(self.numWordsLeft) +\
                         ", # slices " + str(slicesNeeded) + ", earliest stage " +\
                         str(earliest))
                

            while self.numWordsLeft > 0 and self.currentStage < self.switch.numStages:
                self.slRange, self.rowRange = self.getNextRange()
                if any ([len(self.slRange)==0, len(self.rowRange)==0]):
                    logging.debug("next range is empty, switchToNextstage()")
                    self.switchToNextStage()                   
                    continue
                else:
                    logging.debug("assigning rows to table")
                    self.assignRowsToTable()
                    pass
                pass
            
            if (self.numWordsLeft == 0 and self.currentStage < self.switch.numStages):
                logging.debug("Finished " + self.table)
                self.assigned[self.table] = self.currentStage
                pass

            if (self.numWordsLeft > 0):
                self.results['solved'] = False
                logging.warn("No more memory for " + self.table)
                pass
            pass

        if self.table == 'end':
            self.assigned['end'] = -1
            pass
        
        numAssigned = len(self.assigned)
        numTables = len(self.program.names) 
        
        
        logging.debug(str(numAssigned) + " out of " + str(numTables+2))
        logging.info("Tables assigned in order (tableName, earliestSt)- %s " %\
                        nextTables)
        if 'start' in self.assigned:
            numAssigned -= 1
            pass
        if 'end' in self.assigned:
            numAssigned -= 1
            pass
        self.numAssigned = numAssigned
        self.numTables = numTables
        
        config = FlexpipeConfiguration(program=self.program, switch=self.switch,\
                                      preprocess=self.preprocess, version="Greedy")
        config.configure(self.startRowDict, self.numberOfRowsDict)
        logging.debug("done")

        for mem in self.switch.memoryTypes:
            order = 0
            
            self.results['usedSlices'+mem] =\
                int(sum([1 for sl in range(sum(self.switch.numSlices[mem])) if\
                             any([round(self.numberOfRowsDict[mem][log, sl]) > 0\
                                     for log in range(self.numTables)])]))
            pass

        self.results['totalUsedSlices'] =\
            sum([self.results['usedSlices'+mem]\
                     for mem in self.switch.memoryTypes])

        configs = {}
        configs['greedyConfig'] = config
        return configs
