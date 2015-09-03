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



from pycpx import CPlexModel
import rmt_ffd_compiler
import rmt_ffl_compiler
from rmt_configuration import RmtConfiguration
import numpy as np
from datetime import datetime
import time
import logging
"""
Assign number of blocks for each layout, compute number
of logical words from blocks.
"""

class RmtIlpCompiler:
    def __init__(self, relativeGap, greedyVersion,objectiveStr='maximumStage',\
                     emphasis=0, timeLimit=None, treeLimit=None,\
                     variableSelect=None, ignoreConstraint=None,\
                     workMem=None,\
                     nodeFileInd=None,\
                     workDir=None):
        self.logger = logging.getLogger(__name__)

        self.objectiveStr=objectiveStr
        self.relativeGap = relativeGap
        self.greedyVersion = greedyVersion
        self.emphasis = emphasis
        self.variableSelect = variableSelect
        self.timeLimit = timeLimit
        self.treeLimit = treeLimit
        self.workMem = workMem
        self.nodeFileInd = nodeFileInd
        self.workDir = workDir

        self.ignoreConstraint = ignoreConstraint
        self.dictNumVariables = \
            {'log': 0, 'st': 0, 'log*st': 0,
             'allMem*pf*log*st':0,
             'mem*log':0, 'mem*log*st': 0, 'mem*st':0, 'allMem*log*st': 0,
             'constant': 0,
             'succDep':0, 'matchDep':0, 'actionDep':0
            }
        self.numVariables = 0
        self.dictNumConstraints = \
            {'log': 0, 'st': 0, 'log*st': 0,
             'allMem*pf*log*st':0,
             'mem*log':0, 'mem*log*st': 0, 'mem*st':0, 'allMem*log*st': 0,
             'constant': 0,
             'succDep':0, 'matchDep':0, 'actionDep':0
            }
        self.numConstraints = 0
        self.dimensionSizes = {}
        self.logger = self.logger.getLogger(__name__)
        pass

    def setDimensionSizes(self):
        item_count_allmempflogst = 0
        for thing in self.switch.allTypes:
            item_count_allmempflogst += self.pfMax[thing]*self.logMax*self.stMax
        self.dimensionSizes = {
            'log':self.logMax,
            'st':self.stMax,
            'log*st':self.logMax*self.stMax,
            'allMem*pf*log*st':item_count_allmempflogst,
            'mem*log':len(self.switch.memoryTypes)*self.logMax,
            'mem*log*st': len(self.switch.memoryTypes)*self.logMax*self.stMax,
            'mem*st':len(self.switch.memoryTypes)*self.stMax,
            'allMem*log*st': len(self.switch.allTypes)*self.logMax*self.stMax,
            'constant': 1,
            'succDep':len(self.program.logicalSuccessorDependencyList),
            'matchDep':len(self.program.logicalMatchDependencyList),
            'actionDep':len(self.program.logicalActionDependencyList)
        }
        pass

    def computeSum(self, dictCount):
        log_list = []
        compute_value = 0
        for key in dictCount:
            log_list.append('%d*%s(%d)' % \
                (dictCount[key], key, self.dimensionSizes[key]))
            compute_value += dictCount[key] * self.dimensionSizes[key]
        self.logger.info("%s = %d" % (" + ".join(log_list), compute_value))

        return compute_value

    def P(self, l, m):
        return l - m

    def actionAssignmentConstraint(self):
        """
        How many action words we can fit.
        """
        for log in range(self.logMax):
            for st in range(self.stMax):
                if self.preprocess.actionWidths[log] == 0:
                    self.m.constrain(self.word['action'][log,st] <= 0)
                    pass
                else:
                    self.m.constrain(self.word['action'][log,st] >=\
                                         self.word['sram'][log,st] +\
                                         self.word['tcam'][log,st])
                    pass
                pass
            pass
        self.dictNumConstraints['log*st'] += 1
        pass

    def capacityConstraint(self):
        """
        TODO(lav): Add action blocks, stat blocks for log. in this stage,
        TCAM overhead blocks.
        """
        for mem in self.switch.memoryTypes:
            self.m.constrain(self.block[mem].T * np.ones(self.logMax)\
                                 <= self.switch.numSlices[mem])
            pass
        self.dictNumConstraints['mem*st'] += 1

        mem = 'sram'
        self.m.constrain(sum([self.block[thing].T for thing in self.switch.typesIn[mem]])
                             * np.ones(self.logMax)\
                                 <= self.switch.numSlices[mem])
        self.dictNumConstraints['st'] += 1
        pass


    def wordLayoutConstraint(self):
        for mem in self.switch.allTypes:
            for log in range(self.logMax):
                for st in range(self.stMax):
                    self.m.constrain(self.block[mem][log,st] ==\
                                         self.layout[mem][log*self.stMax+st, :] *\
                                         self.preprocess.layout[mem][log])

                    self.m.constrain(self.word[mem][log,st] ==\
                                         self.layout[mem][log*self.stMax+st,:] *\
                                         self.preprocess.word[mem][log])
                    pass
                pass
            pass
        self.dictNumConstraints['allMem*log*st'] += 2
        pass
    
    def useMemoryConstraint(self):
        upperBound = self.blockMax * self.stMax
        # assign blocks of logical table to mem only if it's allowed
        for mem in self.switch.memoryTypes:
            for log in range(self.logMax):
                blocksUsedForLog = (self.block[mem][log,:] *\
                    np.ones((self.stMax)))[0,0]
                blocksAllowedForLog = (upperBound *\
                                           self.preprocess.use[mem][log])
                self.m.constrain(blocksUsedForLog <= blocksAllowedForLog)
                pass
            pass
        self.dictNumConstraints['mem*log'] += 1
        pass
    
    def assignmentConstraint(self):
        allocatedWords = sum([self.word[mem] for mem in\
                                  self.switch.memoryTypes])\
                                  * np.ones(self.stMax)
        self.m.constrain(allocatedWords >= self.program.logicalTables)
        self.dictNumConstraints['log'] += 1
        pass

    def pipelineLatencyVariables(self):
        ub = self.stMax * self.switch.matchDelay
        ubb = self.stMax * self.switch.matchDelay * self.stMax
        self.startTimeOfStage =\
            self.m.new((self.stMax), vtype='real', lb=0, ub=ub,\
                           name='startTimeOfStage')
        self.dictNumVariables['st'] += 1

        self.startAllMemTimesStartTimeOfStage =\
            self.m.new((self.logMax, self.stMax), vtype='real', lb=0, ub = ubb,\
                           name='startAllMemTimesStartTimeOfStage')
        self.endAllMemTimesStartTimeOfStage =\
            self.m.new((self.logMax, self.stMax), vtype='real', lb=0, ub = ubb,\
                           name='endAllMemTimesStartTimeOfStage')
        self.dictNumVariables['log*st'] += 2

        pass

    def getStartAllMemTimesStartTimeOfStage(self):
        # Get startTimeOfStageTimesStartAllMem
        # upper bound of start time of stage 
        upperBound = self.stMax * self.switch.matchDelay * self.stMax
        
        for log in range(self.logMax):
            for st in range(self.stMax):
                self.m.constrain(self.startAllMemTimesStartTimeOfStage[log, st] <=\
                                     self.startAllMem[log,st] * upperBound)
                self.m.constrain(self.startAllMemTimesStartTimeOfStage[log, st] <=\
                                     self.startTimeOfStage[st] +\
                                      (1 - self.startAllMem[log,st]) * upperBound)                
                self.m.constrain(self.startAllMemTimesStartTimeOfStage[log, st] >=\
                                     self.startTimeOfStage[st] -\
                                     (1 - self.startAllMem[log,st]) * upperBound)

                pass
            pass
        self.dictNumConstraints['log*st'] += 3
        pass

    def getEndAllMemTimesStartTimeOfStage(self):
        # Get startTimeOfStageTimesStartAllMem
        # upper bound of start time of stage 
        upperBound = self.stMax * self.switch.matchDelay * self.stMax
        
        for log in range(self.logMax):
            for st in range(self.stMax):
                self.m.constrain(self.endAllMemTimesStartTimeOfStage[log, st] <=\
                                     self.endAllMem[log,st] * upperBound)
                self.m.constrain(self.endAllMemTimesStartTimeOfStage[log, st] <=\
                                     self.startTimeOfStage[st] +\
                                     (1 - self.endAllMem[log,st]) * upperBound)                
                self.m.constrain(self.endAllMemTimesStartTimeOfStage[log, st] >=\
                                     self.startTimeOfStage[st] -\
                                     (1 - self.endAllMem[log,st]) * upperBound)

                pass
            pass
        self.dictNumConstraints['log*st'] += 3
        pass

    def checkPipelineLatencyConstraint(self, model):
        startAllMemTimesStartTimeOfStage = model[self.startAllMemTimesStartTimeOfStage]
        endAllMemTimesStartTimeOfStage = model[self.endAllMemTimesStartTimeOfStage]
        startTimeOfStage = model[self.startTimeOfStage]

        layout = {}
        layout['sram'] = model[self.layout['sram']]
        layout['tcam'] = model[self.layout['tcam']]
        layout['action'] = model[self.layout['action']]

        stageInfo = "\nStart time for model\n"
        for st in range(self.stMax):
             stageInfo += " Stage %d: %.1f " % (st, startTimeOfStage[st])
             tablesThatStart = [log for log in range(self.logMax)\
                                    if startAllMemTimesStartTimeOfStage[log, st] > 0]
             tableInfo = {}
             for log in range(self.logMax):
                 punits = {}
                 for thing in ['sram','tcam','action']:
                     punits[thing] = sum([layout[thing][log*self.stMax+st,pf] for pf in range(self.pfMax[thing])])
                     pass
                 tableInfo[log] = ", ".join(["%s: %d" % (t[0], punits[t]) for t in ['sram','tcam','action']])
                 pass

             stageInfo += "Tables that start in this stage: %s\n" %\
                 ", ".join(["%s: %s" % (self.program.names[log], tableInfo[log]) for log in tablesThatStart])
             pass
        
        self.logger.info(stageInfo)

        startTimeOfStartStageOfLog = {}
        startTimeOfEndStageOfLog = {}
        for log in range(self.logMax):
            startTimeOfStartStageOfLog[log] = \
              sum([startAllMemTimesStartTimeOfStage[log, st] for st in range(self.stMax)])
            startTimeOfEndStageOfLog[log] = \
              sum([endAllMemTimesStartTimeOfStage[log, st] for st in range(self.stMax)])
            pass
                                       
        # successor dependency
        for st in range(1,self.stMax):
            if not (startTimeOfStage[st] >=\
                             startTimeOfStage[st-1] + self.switch.successorDelay):
                roundOkay = (round(startTimeOfStage[st]) >=\
                             round(startTimeOfStage[st-1]) + self.switch.successorDelay)
                level = self.logger.WARNING
                if not roundOkay:
                    level = self.logger.ERROR
                    pass

                self.logger.log(level, "successor dependency constraint on latency violated at %d" % st)
            pass
        
        # match dependency
        for (log1,log2) in self.program.logicalMatchDependencyList:
            if not(startTimeOfStartStageOfLog[log2] >=\
                   startTimeOfEndStageOfLog[log1] + self.switch.matchDelay):
                roundOkay = (round(startTimeOfStartStageOfLog[log2]) >=\
                                 round(startTimeOfEndStageOfLog[log1]) + self.switch.matchDelay)
                level = self.logger.WARNING
                if not roundOkay:
                    level = self.logger.ERROR
                    pass
                self.logger.log(level,\
                                    "match dependency (%s, %s)" % (self.program.names[log1], self.program.names[log2])\
                                    + " on latency violated:"\
                                    + " %s end stage starts at time %d." % ( self.program.names[log1], startTimeOfEndStageOfLog[log1])\
                                    + " %s start stage starts at time %d." % ( self.program.names[log2], startTimeOfStartStageOfLog[log2]))
                pass
            pass

        # action dependency
        for (log1,log2) in self.program.logicalActionDependencyList:
            if not(startTimeOfStartStageOfLog[log2] >=\
                   startTimeOfEndStageOfLog[log1] + self.switch.actionDelay):
                roundOkay = (round(startTimeOfStartStageOfLog[log2]) >=\
                                 round(startTimeOfEndStageOfLog[log1]) + self.switch.actionDelay)
                level = self.logger.WARNING
                if not roundOkay:
                    level = self.logger.ERROR
                    pass

                self.logger.log(level,\
                                    "action dependency (%s, %s) " % (self.program.names[log1], self.program.names[log2])\
                                 + " on latency violated:"\
                                 + " %s end stage starts at time %d." % ( self.program.names[log1], startTimeOfEndStageOfLog[log1])\
                                 + " %s end start starts at time %d." % ( self.program.names[log2], startTimeOfStartStageOfLog[log2]))
                pass
            pass

                    
        pass

    def pipelineLatencyConstraint(self):
        self.startTimeOfStartStageOfLog = {}
        self.startTimeOfEndStageOfLog = {}
        for log in range(self.logMax):
            self.startTimeOfStartStageOfLog[log] = \
                sum([self.startAllMemTimesStartTimeOfStage[log, st] for st in range(self.stMax)])
            self.startTimeOfEndStageOfLog[log] = \
                sum([self.endAllMemTimesStartTimeOfStage[log, st] for st in range(self.stMax)])
            pass
        
        # successor dependency
        for st in range(1,self.stMax):
            self.m.constrain(self.startTimeOfStage[st] >=\
                             self.startTimeOfStage[st-1] + self.switch.successorDelay)
            pass
        self.dictNumConstraints['st'] += 1
        self.dictNumConstraints['constant'] -= 1
        
        # match dependency
        for (log1,log2) in self.program.logicalMatchDependencyList:
            self.m.constrain(\
                             self.startTimeOfStartStageOfLog[log2] >=\
                             self.startTimeOfEndStageOfLog[log1] + self.switch.matchDelay)
            pass
        self.dictNumConstraints['matchDep'] += 1

        # action dependency
        for (log1,log2) in self.program.logicalActionDependencyList:
            self.m.constrain(\
                             self.startTimeOfStartStageOfLog[log2] >=\
                             self.startTimeOfEndStageOfLog[log1] + self.switch.actionDelay)
            pass
        
        self.dictNumConstraints['actionDep'] += 1
        pass
        
    def checkStartingAndEndingStagesConstraint(self, model):
        blockAllMemBin = model[self.blockAllMemBin]
        endAllMem= model[self.endAllMem]
        startAllMem=model[self.startAllMem]
        startAllMemTimesBlockAllMemBin = model[self.startAllMemTimesBlockAllMemBin]
        endAllMemTimesBlockAllMemBin = model[self.endAllMemTimesBlockAllMemBin]
        for log in range(self.logMax):
            if not(sum([endAllMem[log,st] for st in range(self.stMax)]) == 1):
                roundOkay = (sum([round(endAllMem[log,st]) for st in range(self.stMax)]) == 1)
                level = self.logger.WARNING
                if not roundOkay:
                    level = self.logger.ERROR
                    pass
                self.logger.log(level, "Constraint violated- more/less than one end stage for " + self.program.names[log])
                pass
            if not(sum([startAllMem[log,st] for st in range(self.stMax)]) == 1):
                roundOkay = (sum([round(startAllMem[log,st]) for st in range(self.stMax)]) == 1)
                level = self.logger.WARNING
                if not roundOkay:
                    level = self.logger.ERROR
                    pass
                self.logger.log(level, "Constraint violated- more/less than one start stage for " + self.program.names[log])
                pass
            pass
        pass

    def displayActiveRams(self, model):
        """
        For each table in each stage, 
        - number of RAMs for a match packing units (enforce one type per st)
        - + number of RAMs for an action packing unit
        """
        self.logger.info("DISPLAY ACTIVE RAMS")
        ramsForPUnits = 0
        for st in range(self.stMax):
            for log in range(self.logMax):
                name = self.program.names[log]
                # match RAM
                for pf in range(self.pfMax['sram']):
                    ramsPerPUnit = self.preprocess.layout['sram'][log][pf]
                    index = log*self.stMax+st
                    numPUnits = round(model[self.layout['sram']][index, pf])
                    present = round(model[self.layoutBin['sram']][index, pf])

                    idStr = "%d-wide match SRAM PUnit, %s in st %d (pf=%d)"%\
                        (ramsPerPUnit, name, st, pf)
                    layoutStr = "layout (%d) and layoutBin (%d)" %\
                        (numPUnits, present)

                    if numPUnits > 0 and present == 0 or\
                            numPUnits == 0 and present == 1:
                        self.logger.warn( "%s inconsistent for %s" %\
                                          (layoutStr, idStr))
                        pass
                    elif numPUnits > 0 and present > 0:
                        self.logger.info(idStr)
                        ramsForPUnits += ramsPerPUnit
                        pass
                    pass
                # action RAM
                pf = 0
                ramsPerPUnit = self.preprocess.layout['action'][log][pf]
                numPUnits = round(model[self.layout['action']][index, pf])
                present = round(model[\
                    self.layoutBin['action']][log*self.stMax+st, pf])
                idStr = "%d-wide action SRAM PUnit, %s in st %d (pf=%d)"%\
                    (ramsPerPUnit, name, st, pf)
                layoutStr = "layout (%d) and layoutBin (%d)" %\
                    (numPUnits, present)
                if numPUnits > 0 and present == 0 or\
                        numPUnits == 0 and present == 1:
                    self.logger.warn( "%s inconsistent for %s" %\
                                      (layoutStr, idStr))
                    pass
                elif numPUnits > 0 and present > 0:
                    self.logger.info(idStr)
                    ramsForPUnits += ramsPerPUnit
                    pass
                
                pass
            self.logger.info("%d active RAMs over all stages" % ramsForPUnits)
            pass
        pass

    def displayStartingAndEndingStages(self, model):
        numStartingStages = {}
        startStage = {}
        anyBlocksInStartStage = {}
        for log in range(self.logMax):
            # there is exactly one starting stage
            numStartingStages[log] = sum([model[self.startAllMem][log,st] for st in range(self.stMax)])
            self.logger.debug(self.program.names[log])
            self.logger.debug(" numStartingStages: " + str(numStartingStages[log]))
            
            startStage[log] = sum([model[self.startAllMem][log,st] * st for st in range(self.stMax)])
            self.logger.debug(" startStage: " + str(startStage[log]))
            
            upperBound = self.stMax
            # if a stage has blocks, starting stage is at least as small
            for st in range(self.stMax):
                totalBlocks =\
                  sum([model[self.block[mem]][log,st] for mem in self.switch.memoryTypes])

                if (startStage[log] > st and totalBlocks > 0):
                    binary = model[self.blockAllMemBin][log,st]
                    roundOkay = not (round(startStage[log]) > st and round(totalBlocks) > 0)
                    level = self.logger.WARNING
                    if not roundOkay:
                        level = self.logger.ERROR
                        pass

                    self.logger.log(level, "startStage def. constraint violated for log %s, st %d: " % (self.program.names[log], st)\
                                     + " Stage %d has %d mem. blocks in bin. %d ." % (st, totalBlocks, binary)\
                                     + " Lhs (start stage) = %d." % startStage[log]\
                                     + " Rhs = %d + (1-%d)*%d." % (st, int(model[self.blockAllMemBin][log,st]), upperBound)\
                                     + " Lhs <= Rhs?")
                    pass
                pass
            pass
            # starting stage has some blocks
            anyBlocksInStartStage[log] = sum([model[self.startAllMemTimesBlockAllMemBin][log,st] for st in range(self.stMax)])
            self.logger.debug(self.program.names[log])
            self.logger.debug(" anyBlocksInStartStage: " + str(anyBlocksInStartStage[log]))
            pass

        pass
    
    def getStartingAndEndingStages(self):      
        for log in range(self.logMax):
            # there is exactly one starting stage
            self.m.constrain(sum([self.startAllMem[log,st] for st in range(self.stMax)]) == 1)
            
            startStage = sum([self.startAllMem[log,st] * st for st in range(self.stMax)])
            upperBound = self.stMax
            # if a stage has blocks, starting stage is at least as small
            for st in range(self.stMax):
                self.m.constrain(startStage <= st + (1 - self.blockAllMemBin[log,st]) * upperBound)
                pass
            pass

            # starting stage has some blocks
            anyBlocksInStartStage = sum([self.startAllMemTimesBlockAllMemBin[log,st] for st in range(self.stMax)])
            self.m.constrain(anyBlocksInStartStage >= 1)
            pass

        for log in range(self.logMax):
            # there is exactly one ending stage
            self.m.constrain(sum([self.endAllMem[log,st] for st in range(self.stMax)]) == 1)
            
            endStage = sum([self.endAllMem[log,st] * st for st in range(self.stMax)])
            upperBound = self.stMax
            # if a stage has blocks, ending stage is at least as big
            for st in range(self.stMax):
                self.m.constrain(endStage >= st - (1 - self.blockAllMemBin[log,st]) * upperBound)
                pass
            pass
            # ending stage has some blocks
            anyBlocksInEndStage = sum([self.endAllMemTimesBlockAllMemBin[log,st] for st in range(self.stMax)])
            self.m.constrain(anyBlocksInEndStage >= 1)
            pass
        self.dictNumConstraints['log'] += 2*2
        self.dictNumConstraints['log*st'] += 2
        pass

    def dependencyConstraint(self):
        """
        If log2 action depends on log1, then last stage (any mem)
        of log1 is strictly before first stage (any mem) of log2.
        """
        eps = 0.01
        upperBound = self.stMax
        allStages = np.matrix(self.preprocess.toposortOrderStages).T

        for (log1,log2) in self.program.logicalSuccessorDependencyList:
            start2 = self.startAllMem[log2, :] * allStages
            end1 = self.endAllMem[log1,:] * allStages
            self.m.constrain(start2 >= end1)
            pass
        self.dictNumConstraints['succDep'] += 1

        for (log1,log2) in self.program.logicalMatchDependencyList:
            start2 = self.startAllMem[log2, :] * allStages
            end1 = self.endAllMem[log1,:] * allStages
            self.m.constrain(start2 >= eps + end1)
            pass
        self.dictNumConstraints['matchDep'] += 1

        for (log1,log2) in self.program.logicalActionDependencyList:
            start2 = self.startAllMem[log2, :] * allStages
            end1 = self.endAllMem[log1,:] * allStages
            self.m.constrain(start2 >= eps + end1)
            pass
        self.dictNumConstraints['actionDep'] += 1


        pass
    
    def maximumStageConstraint(self):
        # minimize maximum stage
        upperBound = self.blockMax
        lowerBound = 1

        # Binary constraint
        for st in range(self.stMax):
            # totalBlocksForStBin doesn't count action RAMs
            total = sum([self.block[mem][log,st]\
                             for log in range(self.logMax)\
                             for mem in self.switch.memoryTypes])
            self.m.constrain(total <= upperBound *\
                                 self.totalBlocksForStBin[st])
            self.m.constrain(total >= lowerBound *\
                                 self.totalBlocksForStBin[st])
            pass

        
        upperBound = self.stMax
        maximumStage = sum([self.isMaximumStage[st]*st\
                                for st in range(self.stMax)])
        # If a stage st has blocks, maximumStage at least as big as st
        for st in range(self.stMax):
            self.m.constrain(self.totalBlocksForStBin[st] * st <=\
                                 maximumStage)
            pass

        # Exactly one stage can be maximum stage
        numMaxStages = sum([self.isMaximumStage[st] for st in\
                                range(self.stMax)])
        self.m.constrain(numMaxStages == 1)

        # Product constraint
        for st in range(self.stMax):
            self.m.constrain(\
                self.isMaximumStageTimesTotalBlocksForStBin[st] <=\
                    self.totalBlocksForStBin[st])
            self.m.constrain(\
                self.isMaximumStageTimesTotalBlocksForStBin[st] <=\
                    self.isMaximumStage[st])
            self.m.constrain(\
                self.isMaximumStageTimesTotalBlocksForStBin[st] >=\
                    self.totalBlocksForStBin[st]+\
                    self.isMaximumStage[st]-1)
            pass

        # Maximum stage has one or more blocks
        sumOverSt =\
            sum([self.isMaximumStageTimesTotalBlocksForStBin[st]\
                     for st in range(self.stMax)])
        self.m.constrain(sumOverSt > 0)

        self.dictNumConstraints['st'] += 6 
        # 2 for bin, 1 for "at least as big", 3 for prod
        self.dictNumConstraints['constant'] += 2
        # 1 for numMaxStages, 1 for max stage has non zero blocks
        pass

    def getBlockBinary(self):
        lowerBound = 1
        for mem in self.switch.memoryTypes:
            upperBound = sum(self.switch.numSlices[mem])
            for log in range(self.logMax):
                for st in range(self.stMax):
                    self.m.constrain(self.blockBin[mem][log,st]*lowerBound <=\
                                         self.block[mem][log,st])
                    self.m.constrain(self.blockBin[mem][log,st]*upperBound\
                                         >= self.block[mem][log,st])
                    pass
                pass
            pass
        self.dictNumConstraints['mem*log*st'] += 2
        pass

    def getLayoutBinary(self):
        lowerBound = 1
        for thing in self.switch.allTypes:
            upperBound = self.blockMax 
            for log in range(self.logMax):
                for st in range(self.stMax):
                    for pf in range(self.pfMax[thing]):
                        index = log*self.stMax + st
                        self.m.constrain(\
                            self.layoutBin[thing][index, pf]*lowerBound <=\
                                self.layout[thing][index, pf])
                        self.m.constrain(\
                            self.layoutBin[thing][index, pf]*upperBound\
                                >= self.layout[thing][index, pf])
                        pass
                    pass
                pass
            pass
        self.dictNumConstraints['allMem*pf*log*st'] += 1

    def checkInputCrossbarConstraint(self, model, mem):
        blockBin = model[self.blockBin[mem]]
        numSubunitsNeeded = {}
        numSubunitsAvailable = {}

        for st in range(self.stMax):
            numSubunitsNeeded = sum([blockBin[log,st] *\
                                     self.preprocess.inputCrossbarNumSubunits[mem][log] for log in range(self.logMax)])
            numSubunitsAvailable = self.switch.inputCrossbarNumSubunits[mem] 
            if (numSubunitsNeeded > numSubunitsAvailable):
                roundOkay = (sum([round(blockBin[log,st]) *\
                                     self.preprocess.inputCrossbarNumSubunits[mem][log] for log in range(self.logMax)])\
                                     <= numSubunitsAvailable)
                level = self.logger.WARNING
                if not roundOkay:
                    level = self.logger.ERROR
                    pass

                self.logger.log(level, "Input Crossbar Constraint violated in st %d, mem %s" % (st,mem) +\
                             "Used " + str(numSubunitsNeeded) +", Available " + str(numSubunitsAvailable))
                pass
            pass        
        pass

    def inputCrossbarConstraint(self):
        numSubunitsNeeded = {}
        numSubunitsAvailable = {}
        for mem in self.switch.memoryTypes:
            numSubunitsNeeded[mem] = self.blockBin[mem].T *\
                self.preprocess.inputCrossbarNumSubunits[mem]
            numSubunitsAvailable[mem] =\
                self.switch.inputCrossbarNumSubunits[mem] *\
                np.ones((self.stMax,1))
            self.m.constrain(numSubunitsNeeded[mem] <=\
                                 numSubunitsAvailable[mem])
            pass        
        self.dictNumConstraints['mem*st'] += 1
        pass

    def getBlockAllMemBinary(self):
        lowerBound = 1
        upperBound = sum([self.switch.numSlices[mem] for mem in\
                              self.switch.memoryTypes])
        for log in range(self.logMax):
            for st in range(self.stMax):
                # blockAllMemBin doesn't count action RAMs
                total = sum([self.block[mem][log,st] for\
                                 mem in self.all])
                self.m.constrain(total <= upperBound[st] *\
                                     self.blockAllMemBin[log,st])
                self.m.constrain(total >= lowerBound *\
                                     self.blockAllMemBin[log,st])
                pass
            pass
        self.dictNumConstraints['log*st'] += 2
        pass

    def resolutionLogicConstraint(self):
        numMatchTablesUsed = self.blockAllMemBin.T * np.ones((self.logMax,1))
        numMatchTablesAvailable = self.switch.resolutionLogicNumMatchTables *\
            np.ones((self.stMax,1))
        self.m.constrain(numMatchTablesUsed <= numMatchTablesAvailable)
        self.dictNumConstraints['st'] += 1
        pass

    def actionCrossbarConstraint(self):
        """
        No more than 1280 bits of action from each stage.
        """
        numTotalBitsAvailable = self.switch.actionCrossbarNumBits *\
            np.ones((self.stMax,1))
        numTotalBitsNeeded = self.blockAllMemBin.T *\
            self.preprocess.actionCrossbarNumBits
        self.m.constrain(numTotalBitsNeeded <= numTotalBitsAvailable)
        self.dictNumConstraints['st'] += 1
        pass

    def onePackingUnitForLogInStage(self):
        for st in range(self.stMax):
            for log in range(self.logMax):
                index = log*self.stMax+st
                numPUnitTypesForLogInSt = sum([\
                        self.layoutBin['sram'][index, pf]\
                            for pf in range(self.pfMax['sram'])])
                self.m.constrain(numPUnitTypesForLogInSt <= 1)
                pass
            pass
        self.dictNumConstraints['log*st'] += 1
        pass

    def getNumActiveSrams(self):
        """
        For each table in each stage, 
        - number of RAMs for a match packing units (enforce one type per st)
        - + number of RAMs for an action packing unit
        """
        ramsForPUnits = 0
        for st in range(self.stMax):
            for log in range(self.logMax):
                # match RAM
                for pf in range(self.pfMax['sram']):
                    ramsPerPUnit = self.preprocess.layout['sram'][log][pf]
                    present = self.layoutBin['sram'][log*self.stMax+st, pf]
                    ramsForPUnits += present * ramsPerPUnit
                    pass
                # action RAM
                pf = 0
                ramsPerPUnit = self.preprocess.layout['action'][log][pf]
                present = self.layoutBin['action'][log*self.stMax+st, pf]
                ramsForPUnits += present * ramsPerPUnit
                pass
            pass
        self.numActiveSrams = ramsForPUnits
        pass

    def getNumActiveTcams(self):
        """
        If match data width is less than TCAM width, only 
        a fraction of TCAM is active/ consumes power.
        """
        tcamsForPUnits = 0
        for st in range(self.stMax):
            for log in range(self.logMax):
                for pf in range(self.pfMax['tcam']):
                    # layout['tcam'][log] is not a list, just an int
                    tcamsPerPUnit = self.preprocess.layout['tcam'][log]
                    tcamWidth = tcamsPerPUnit * self.switch.width['tcam']
                    matchWidth = self.program.logicalTableWidths[log]
                    numPUnits = self.layout['tcam'][log*self.stMax+st, pf]
                    tcamsForPUnits += numPUnits * (tcamWidth/matchWidth)
                    pass
                pass
            pass
        self.numActiveTcams = tcamsForPUnits
        pass

    def getPowerForRamsAndTcamsObjective(self):
        self.getNumActiveSrams()
        self.getNumActiveTcams()
        self.powerForRamsAndTcams =\
            self.switch.power['wattsPerTcam'] * self.numActiveTcams +\
            self.switch.power['wattsPerSram'] * self.numActiveSrams
        pass

    
    def startAndEndStagesVariables(self):
        logMax = self.logMax
        stMax = self.stMax

        self.startAllMem = self.m.new((logMax, stMax), vtype=bool,\
          name='startAllMem')
        self.dictNumVariables['log*st'] += 1

        self.startAllMemTimesBlockAllMemBin =  self.m.new((logMax, stMax), vtype=bool,\
                                                          name='startAllMemTimesBlockAllMemBin')                   
        self.dictNumVariables['log*st'] += 1

        self.endAllMem = self.m.new((logMax, stMax), vtype=bool,\
          name='endAllMem')
        self.dictNumVariables['log*st'] += 1

        self.endAllMemTimesBlockAllMemBin =  self.m.new((logMax, stMax), vtype=bool,\
                                                          name='endAllMemTimesBlockAllMemBin')                   
        self.dictNumVariables['log*st'] += 1
        pass

    def getXxAllMemTimesBlockAllMemBin(self):
        for log in range(self.logMax):
            for st in range(self.stMax):
                self.m.constrain(self.startAllMemTimesBlockAllMemBin[log, st] <= self.startAllMem[log, st])
                self.m.constrain(self.startAllMemTimesBlockAllMemBin[log, st] <= self.blockAllMemBin[log, st])
                self.m.constrain(self.startAllMemTimesBlockAllMemBin[log, st] >= self.startAllMem[log, st] +\
                                 self.blockAllMemBin[log, st] - 1)
                pass
            pass

        for log in range(self.logMax):
            for st in range(self.stMax):
                self.m.constrain(self.endAllMemTimesBlockAllMemBin[log, st] <= self.endAllMem[log, st])
                self.m.constrain(self.endAllMemTimesBlockAllMemBin[log, st] <= self.blockAllMemBin[log, st])
                self.m.constrain(self.endAllMemTimesBlockAllMemBin[log, st] >= self.endAllMem[log, st] +\
                                 self.blockAllMemBin[log, st] - 1)
                pass
            pass
        self.dictNumConstraints['log*st'] += 6
        pass

    def getIlpStartingDictValues(self, block, layout, word,\
                                     startTimeOfStage):

        usedStage = {}
        totalBlocksForStBin = np.zeros(self.stMax)
        isMaximumStage = np.zeros(self.stMax)
        isMaximumStageTimesTotalBlocksForStBin = np.zeros(self.stMax)
        maximumStage = -1
    
        for mem in self.switch.memoryTypes:
            for st in range(self.stMax):
                if sum([block[mem][log,st] for mem in self.all\
                            for log in range(self.logMax)]) > 0:
                    if st > maximumStage:
                        maximumStage = st
                        pass
                    totalBlocksForStBin[st] = 1              
                    pass
                pass
            pass

        self.logger.info(\
       "Maximum stage in start solution is %.1f.." % maximumStage)
        isMaximumStage[maximumStage] = 1
        isMaximumStageTimesTotalBlocksForStBin[maximumStage] = 1

        self.startingDict[self.totalBlocksForStBin] = totalBlocksForStBin
        self.startingDict[self.isMaximumStage] = isMaximumStage
        self.startingDict[self.isMaximumStageTimesTotalBlocksForStBin] =\
            isMaximumStageTimesTotalBlocksForStBin

        blockBin = {}
        for thing in self.switch.allTypes:
            blockBin[thing] = np.zeros((self.logMax, self.stMax))            
            for log in range(self.logMax):
                for st in range(self.stMax):
                    if block[thing][log,st] > 0:
                        blockBin[thing][log,st] = 1
                        pass
                    pass
                pass
            pass

        layoutBin = {}
        for thing in self.switch.allTypes:
            width = int(self.logMax*self.stMax)
            depth = int(self.pfMax[thing])
            layoutBin[thing] = np.zeros((width, depth))
            for log in range(self.logMax):
                for st in range(self.stMax):
                    for pf in range(self.pfMax[thing]):
                        if layout[thing][log*self.stMax+st,pf] > 0:
                            layoutBin[thing][log*self.stMax+st,pf] = 1
                            pass
                        pass
                    pass
                pass
            pass
              
        for thing in self.switch.allTypes:
            self.startingDict[self.word[thing]] = word[thing]
            self.startingDict[self.block[thing]] = block[thing]
            self.startingDict[self.layout[thing]] = layout[thing]
            self.startingDict[self.blockBin[thing]] = blockBin[thing]
            self.startingDict[self.layoutBin[thing]] = layoutBin[thing]
            pass

        self.startingDict[self.startTimeOfStage] =\
            startTimeOfStage


        blockAllMemBin = np.zeros((self.logMax, self.stMax))
        for log in range(self.logMax):
            for st in range(self.stMax):
                totalBlocks = sum([round(block[mem][log,st]) for mem in self.all])
                if totalBlocks > 0:
                    blockAllMemBin[log,st] = 1
                pass
                pass
            pass
        self.startingDict[self.blockAllMemBin] = blockAllMemBin
        
        startAllMem = np.zeros((self.logMax, self.stMax))
        endAllMem = np.zeros((self.logMax, self.stMax))

        startAllMemTimesStartTimeOfStage = np.zeros((self.logMax, self.stMax))
        endAllMemTimesStartTimeOfStage = np.zeros((self.logMax, self.stMax))

        startAllMemTimesBlockAllMemBin = np.zeros((self.logMax, self.stMax))
        endAllMemTimesBlockAllMemBin = np.zeros((self.logMax, self.stMax))

        for log in range(self.logMax):
            stages = [st for st in range(self.stMax)\
                          if any([round(block[mem][log,st])>0\
                                      for mem in self.all])]
            pass
            if len(stages) == 0:
                self.logger.warn("Warning! " + str(log) + " not assigned to any stage")
                pass
            else:
                startSt = int(min(stages))
                endSt = int(max(stages))
                startAllMem[log,startSt] = 1
                endAllMem[log, endSt] = 1
                startAllMemTimesBlockAllMemBin[log, startSt] = blockAllMemBin[log, startSt]
                endAllMemTimesBlockAllMemBin[log, endSt] = blockAllMemBin[log, endSt]
                startAllMemTimesStartTimeOfStage[log,startSt] = startTimeOfStage[startSt]
                endAllMemTimesStartTimeOfStage[log,endSt] = startTimeOfStage[endSt]
                pass
            pass
                
        self.startingDict[self.startAllMem] = startAllMem
        self.startingDict[self.endAllMem] = endAllMem
        self.startingDict[self.startAllMemTimesStartTimeOfStage] =\
          startAllMemTimesStartTimeOfStage
        self.startingDict[self.endAllMemTimesStartTimeOfStage] =\
          endAllMemTimesStartTimeOfStage
        self.startingDict[self.startAllMemTimesBlockAllMemBin] =\
          startAllMemTimesBlockAllMemBin
        self.startingDict[self.endAllMemTimesBlockAllMemBin] =\
          endAllMemTimesBlockAllMemBin
        pass

    def displayMaximumStage(self, model):
        maximumStage = sum([model[self.isMaximumStage][st]*st\
                                for st in range(self.stMax)])
        self.logger.info("maximum stage from model: %.1f" % maximumStage)
        numMaxStages = sum([model[self.isMaximumStage][st] for\
                                st in range(self.stMax)])
        self.logger.info("num maximum stages from model: %.1f" %\
                         numMaxStages)
        sumOverSt =\
            sum([model[self.isMaximumStageTimesTotalBlocksForStBin]\
                     [st] for st in range(self.stMax)])
        self.logger.info(\
            "sum over is max st time totalBlocksForStBin: %.1f" %\
                sumOverSt)
        infoStr =\
            "totalBlocksForStBin, isMaximumStage, "
        infoStr += "total (w/o action), total (w action)\n"
        for st in range(self.stMax):
            totalWoAction = sum([model[self.block[mem]][log,st]\
                             for log in range(self.logMax)\
                             for mem in self.switch.memoryTypes])
            
            totalWAction = totalWoAction +\
                sum([model[self.block['action']][log,st]\
                             for log in range(self.logMax)])
            infoStr +=\
                ("St %d: %.1f, %.1f, %.1f, %.1f\n" %\
                     (\
                    st,\
                        model[self.totalBlocksForStBin][st],\
                        model[self.isMaximumStage][st],\
                        totalWoAction, totalWAction))
            pass
        self.logger.info(infoStr)
        pass
    
        
    def solve(self, program, switch, preprocess):

        solveStart = time.time()
        self.program = program
        self.switch = switch
        self.preprocess = preprocess
        # doesn't count action RAM in allMem,
        # so start/ end/ max stage, latency etc.
        # based only on match RAMs
        self.all = self.switch.memoryTypes
        self.logger.info("Types counted in start/end/max stage, latency: %s" %\
                          self.all)
        ####################################################
        # Constants
        ####################################################
        pfMax = {}
        for mem in self.switch.allTypes:
            pfMax[mem] = preprocess.layout[mem].shape[1]
            pass

        stMax = switch.numStages
        logMax = program.MaximumLogicalTables

        # upper bound on blocks for a table in a stage
        blockMax = int(sum([np.matrix(switch.numSlices[mem]).T\
                                for mem in switch.memoryTypes])[0,0])

        # upper bound on logical words for a table in a stage
        mem = 'sram'
        wordMax = int(switch.depth[mem] * switch.width[mem]\
                          * blockMax)
        


        self.pfMax = pfMax
        self.stMax = stMax
        self.logMax = logMax
        self.blockMax = blockMax
        self.wordMax = wordMax


        ####################################################
        # Variables
        ####################################################
        self.results = {}
        self.results['relativeGap'] = self.relativeGap
        self.results['greedyVersion'] = self.greedyVersion
        self.results['stMax'] = switch.numStages
        
        self.m = CPlexModel(verbosity=3)

        # Per memory per logical table per stage variables
        # 4 * memoryTypes * logMax * stMax

        self.word = {}
        self.block = {}
        self.blockBin = {}
        self.layout = {}
        self.layoutBin = {}

        # Used stage variable memoryTypes * stMax


        for thing in self.switch.allTypes:
            self.word[thing] =\
                self.m.new((logMax, stMax), vtype='real', lb=0, ub=wordMax,\
                          name='word'+thing)
            self.block[thing] =\
                self.m.new((logMax, stMax), vtype='real', lb=0, ub=blockMax,\
                          name='block'+thing)

            self.layout[thing] =\
                self.m.new((logMax * stMax, pfMax[thing]), vtype=int, lb=0,\
                               ub=blockMax, name='layout'+thing)

            self.blockBin[thing]\
                = self.m.new((logMax, stMax), vtype=bool,\
                                 name='blockBin'+thing)
            self.layoutBin[thing]\
                = self.m.new((logMax * stMax, pfMax[thing]), vtype=bool,\
                                 name='layoutBin'+thing)
            pass    
        self.dictNumVariables['allMem*log*st'] += 3
        self.dictNumVariables['allMem*pf*log*st'] += 2

        # Total Blocks per stage logMax * stMax * 2
        self.blockAllMemBin = self.m.new((logMax, stMax), vtype=bool,\
                              name='blockAllMemBin')
        self.dictNumVariables['log*st'] += 1
        
        # Maximum stage variables stMax * 2
        self.isMaximumStage =\
            self.m.new(stMax, vtype=int, lb=0, ub=1, name='isMaximumStage')
        self.totalBlocksForStBin =\
            self.m.new(stMax, vtype=int, lb=0, ub=1,\
                           name='totalBlocksForStBin')
        self.isMaximumStageTimesTotalBlocksForStBin =\
            self.m.new(stMax, vtype=int, lb=0, ub=1,\
                           name='isMaximumStageTimesTotalBlocksForStBin')

        self.dictNumVariables['st'] += 3

        # Starting and ending stage variables logMax * stMax * 3 * 2
        self.startAndEndStagesVariables()
        self.getXxAllMemTimesBlockAllMemBin()
        
        self.pipelineLatencyVariables()
        
        # BASIC CONSTRAINTS
        # Sets block and word variables
        # Blocks and Words for logical table/ stage are consistent with
        # chosen layouts
        self.wordLayoutConstraint()

        # Blocks assigned to match, action etc. in each  stage/ memory don't
        # exceed capacity
        if 'capacity' != self.ignoreConstraint:
            self.capacityConstraint()

        # Use memory type only where allowed
        if 'useMemory' != self.ignoreConstraint:
            self.useMemoryConstraint()

        # Assign enough match words for each table
        if 'assignment' != self.ignoreConstraint:
            self.assignmentConstraint()

        # Get starting and ending stages for logical tables over all memory
        # types
        self.getStartingAndEndingStages()

        # Match, Action, Successor dependency constraint on starting and 
        # ending stages for each logical table
        if 'dependency' != self.ignoreConstraint:
            self.dependencyConstraint()

        # RMT SPECIFIC CONSTRAINTS

        # At least as many action words as match words for a logical table
        # in each stage
        if 'action' != self.ignoreConstraint:
            self.actionAssignmentConstraint()

        self.getBlockBinary()
        # No more than XX subunits used from input crossbar at each stage
        if 'inputCrossbar' != self.ignoreConstraint:
            self.inputCrossbarConstraint()

        self.getBlockAllMemBinary()
        # No more than XX tables matched in each stage
        if 'resolutionLogic' != self.ignoreConstraint:
            self.resolutionLogicConstraint()

        # No more than XX bits used from action crossbar at each stage
        if 'actionCrossbar' != self.ignoreConstraint:
            self.actionCrossbarConstraint()

        self.getStartAllMemTimesStartTimeOfStage()
        self.getEndAllMemTimesStartTimeOfStage()
        if self.ignoreConstraint != 'pipelineLatency' and \
                self.objectiveStr not in ['maximumStage', 'powerForRamsAndTcams']:
            self.pipelineLatencyConstraint()
        else:
            print 'pipelineLatency constraint ignored!!'
        
        self.maximumStageConstraint()

        self.startingDict = {}

        self.logger.debug("Solving ")
        configs = {}
        if len(self.greedyVersion)>0:
            numSramBlocksReserved=int(self.greedyVersion.split("-")[1])
            ####################################################
            self.logger.debug("Getting a greedy solution")
            greedyCompiler = rmt_ffd_compiler.RmtFfdCompiler(numSramBlocksReserved)
            if 'ffl' in self.greedyVersion:
                greedyCompiler = rmt_ffl_compiler.RmtFflCompiler(numSramBlocksReserved)
                pass
            start = time.time()
            greedyConfig =\
                greedyCompiler.solve(self.program, self.switch, self.preprocess)['greedyConfig']
            configs['greedyConfig'] = greedyConfig

            end = time.time()
            ####################################################
            self.logger.debug("Displaying greedy solution")
            greedyConfig.display()
            ####################################################
            self.logger.debug("Saving results from greedy")
            self.results['greedyTotalUnassignedWords'] = greedyCompiler.results['totalUnassignedWords']
            self.results['greedySolveTime'] = greedyCompiler.results['solveTime']
            self.results['greedySolved'] = greedyCompiler.results['solved']
            self.results['greedyPipelineLatency'] = greedyCompiler.results['pipelineLatency']
            self.results['greedyPower'] = greedyCompiler.results['power']
            self.results['greedyNumStages'] = greedyCompiler.results['numStages']
            self.logger.info("results[Greedy .." + str(self.results))

            if not self.results['greedySolved']:
                self.logger.warn("Greedy couldn't fit: " + str(self.results))
                pass

            ####################################################
            self.logger.debug("Starting with Greedy Solution as input")
            self.getIlpStartingDictValues(block=greedyCompiler.block,\
                                          layout=greedyCompiler.layout,\
                                          word=greedyCompiler.word,\
                                          startTimeOfStage=greedyConfig.getStartTimeOfStage())
            self.checkConstraints(self.startingDict)        
            pass

        #totalBlocks = sum(sum([totalBlocks[mem] for mem in switch.memoryTypes]))
        #self.totalBitsInUsedStagesObjective()
        pipelineLatency = self.startTimeOfStage[self.stMax-1]
        totalMemBlocks = sum([self.block[mem].T for mem in self.switch.allTypes])
        totalBlocks = (totalMemBlocks * np.ones(self.logMax)).T * np.ones(self.stMax)
        self.logger.info("Shape of totalMemBlocks %s" % str(totalMemBlocks.shape))
        self.logger.info("Shape of np.ones(self.logMax) %s" % str(np.ones(self.logMax).shape))
        self.logger.info("Shape of np.ones(self.stMax) %s" % str(np.ones(self.stMax).shape))

        maximumLatency = self.switch.matchDelay * self.switch.numStages
        maximumStage = sum([self.isMaximumStage[st]*st\
                                for st in range(self.stMax)])

        self.getLayoutBinary()
        self.onePackingUnitForLogInStage()
        self.getPowerForRamsAndTcamsObjective()
        powerForRamsAndTcams = self.powerForRamsAndTcams
        if self.objectiveStr == 'totalBlocks':
            self.logger.info("Total blocks objective includes action RAMs, though stage/ latency vars don't")
            pass
        totalBlocksAvailable = sum(sum(([self.switch.numSlices[mem] for mem in self.switch.memoryTypes])))
        objectives = {'pipelineLatency+totalBlocks':pipelineLatency/maximumLatency + totalBlocks/totalBlocksAvailable,\
                          'pipelineLatency':pipelineLatency,\
                          'totalBlocks':totalBlocks,\
                          'maximumStage':maximumStage,\
                          'powerForRamsAndTcams':powerForRamsAndTcams}

        solverTimes = []
        nIterations = []
        
        self.setDimensionSizes()
        self.logger.info("Computing variables:")
        self.numVariables = self.computeSum(self.dictNumVariables)
        self.logger.info("Computing Constraints:")
        self.numConstraints = self.computeSum(self.dictNumConstraints)
        self.logger.info("numRows: %d" % self.m.getNRows())
        self.logger.info("numCols: %d" % self.m.getNCols())
        # FIND WHAT THE MINIMUM VALUE FOR OBJECTIVE STR IS
        try:
            self.m.minimize(objectives[self.objectiveStr], starting_dict=self.startingDict,\
                                relative_gap=self.relativeGap,\
                                emphasis=self.emphasis,\
                                time_limit=self.timeLimit,\
                                tree_limit=self.treeLimit,\
                                variable_select=self.variableSelect)
            pass
        except Exception, e:
            self.logger.exception(e)
            pass
        self.checkConstraints(self.m)

        # 3: Emphasize moving best bound: even greater emphasis is placed on proving optimality
        # through moving the best bound value, so that the detection of feasible solutions along
        # the way becomes almost incidental.
        solverTimes.append(self.m.getSolverTime())
        nIterations.append(self.m.getNIterations())
        """
        # MINIMIZE NUMBER OF BLOCKS SUBJECT TO VALUE OF OBJECTIVE STR <= ABOVE
        # OTHERWISE ONLY UPPER BOUND ON NUMBER OF BLOCKS IS FROM CAPACITY CONSTRAINT
        objectiveValue = self.m[objectives[self.objectiveStr]]
        self.m.constrain(objectives[self.objectiveStr] <= objectiveValue)
        self.logger.info("%s <= %.2f" % (self.objectiveStr, objectiveValue))
        
        self.m.minimize(totalBlocks, starting_dict=self.startingDict,\
                            relative_gap=self.relativeGap)
        solverTimes.append(self.m.getSolverTime())
        nIterations.append(self.m.getNIterations())

        
        # MINIMIZE PIPELINE LATENCY SUBJECT TO VALUE OF TOTAL BLOCKS <= ABOVE
        # OTHERWISE NO UPPER BOUND ON START TIME OF LAST STAGE, ONLY LOWER BOUND
        minTotalMemBlocks = sum([self.m[self.block[mem]].T for mem in self.switch.allTypes])
        minTotalBlocks = int(round(sum([minTotalMemBlocks[st,log] for log in range(self.logMax)\
                                  for st in range(self.stMax)])))
        self.logger.info("Total blocks <= %.1f" % minTotalBlocks)
        
        self.m.constrain(totalBlocks <= minTotalBlocks)
        self.m.minimize(pipelineLatency, starting_dict=self.startingDict,\
                            relative_gap=0.9)
        solverTimes.append(self.m.getSolverTime())
        nIterations.append(self.m.getNIterations())
        """
        
        ####################################################
        self.logger.debug("Saving results from ILP")
        self.setIlpResults(solverTimes=solverTimes, nIterations=nIterations)
        ####################################################
        # Logging
        ####################################################                
        m = self.m
        layout = {}
        for thing in self.switch.allTypes:
            layout[thing] = m[self.layout[thing]]
            pass
        config = RmtConfiguration(program=self.program, switch=self.switch, preprocess=self.preprocess,\
                                      layout=layout, version="ILP")
        self.results['ilpTotalUnassignedWordsFromConfig'] = config.totalUnassignedWords
        self.results['ilpPipelineLatencyFromConfig'] = config.getPipelineLatency()
        self.results['ilpPowerFromConfig'] = config.getPowerForRamsAndTcams()
        solveEnd = time.time()
        self.results['solveTime'] = solveEnd - solveStart

        ####################################################
        self.logger.debug("Displaying ILP solution")
        config.display()
        ####################################################
        configs['ilp-%s' % self.objectiveStr] = config
        return configs

    def setIlpResults(self, solverTimes, nIterations):
        totalMemBlocks = sum([self.m[self.block[mem]].T for mem in self.switch.allTypes])
        totalBlocks = int(round(sum([totalMemBlocks[st,log] for log in range(self.logMax)\
                                         for st in range(self.stMax)])))
        self.results['ilpTotalBlocks'] = totalBlocks
        self.results['ilpNumActiveSrams'] = float(self.m[self.numActiveSrams])
        self.results['ilpNumActiveTcams'] = float(self.m[self.numActiveTcams])
        self.results['ilpPower'] = float(self.m[self.powerForRamsAndTcams])
        self.results['ilpPipelineLatency'] = self.m[self.startTimeOfStage][self.stMax-1]
        self.results['ilpTime'] = sum(solverTimes) 
        self.results['ilpNumIterations'] = sum(nIterations) 
        self.results['ilpTimeList'] = ("%s" % solverTimes).replace(",",";")
        self.results['ilpNumIterationsList'] = ("%s" % nIterations).replace(",",";")
        self.results['ilpNumRowsInModel'] = self.m.getNRows()
        self.results['ilpNumColsInModel'] = self.m.getNCols()
        self.results['ilpNumQCsInModel'] = self.m.getNQCs()
        # If you're doing multiple m.minimize, stores last value, unlike NumIterations/ Time list above
        self.results["ilpSolverTime"] = self.m.getSolverTime()
        self.results["ilpNIterations"] = self.m.getNIterations()
        self.results["ilpBestObjValue"] = self.m.getBestObjValue()
        self.results["ilpCutoff"] = self.m.getCutoff()
        self.results["ilpMIPRelativeGap"] = self.m.getMIPRelativeGap()
        self.results["ilpNnodes"] = self.m.getNnodes()

        totalBlocks = np.zeros((self.stMax))
        for st in range(self.stMax):
            totalBlocks[st] = sum([self.m[self.block[mem]][log,st]\
                                   for log in range(self.logMax)\
                                   for mem in self.all])
        pass
        self.results['ilpNumStages'] = max([st for st in range(self.stMax) if\
                                       totalBlocks[st] > 0])+1
        self.results['ilpNumVariables'] = self.numVariables
        self.results['ilpNumConstraints'] = self.numConstraints
        pass
        
    

    def checkConstraints(self,model):
        self.checkPipelineLatencyConstraint(model)
        for mem in self.switch.memoryTypes:
            self.checkInputCrossbarConstraint(model, mem)
            pass
        self.checkStartingAndEndingStagesConstraint(model)
        self.displayStartingAndEndingStages(model)
        self.displayActiveRams(model)
        self.displayMaximumStage(model)
        pass
