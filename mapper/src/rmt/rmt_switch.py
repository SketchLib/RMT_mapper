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



import numpy as np
import logging
"""
RMT switch.
"""


class RmtSwitch:


    # order .. stage number to topo-sort number
    def __init__(self,  numSlices = {'sram':106, 'tcam':16},\
                     depth = {'sram':1000, 'tcam':2000},\
                     width = {'sram':80, 'tcam':40},\
                     numStages = 32,\
                     matchType =\
                     {'sram':['exact'], 'tcam':['exact', 'lpm', 'ternary', 'gw', 'mapper']},\
                     inputCrossbarNumSubunits =\
                     {'sram':8, 'tcam':8},\
                     inputCrossbarWidthSubunit=\
                     {'sram':80,'tcam':80},\
                     actionCrossbarNumBits=1280,\
                     matchTablesPerStage=\
                     {'sram':8, 'tcam':8},\
                     delays= {'match':12, 'action':3, 'successor':1},\
                     power= {'wattsPerSramBit': 16.8090820313e-08,\
                                 'wattsPerTcamBit':5.8520785245e-07},\
                     unpackableMemTypes=['tcam'],\
                     toposortOrder = []):
        self.logger = logging.getLogger(__name__)
        switchInfoStr = "RMT SWITCH"

        self.memoryTypes = sorted([k for k in depth])
        switchInfoStr += ("\nMemory types: %s" % self.memoryTypes)

        self.matchType = matchType
        switchInfoStr += ("\nMatch type: %s" % self.matchType)

        for mem in self.memoryTypes:
            if type(numSlices) == list and\
                    len(numSlices[mem]) != numStages:
                switchInfoStr += ("\nInvalid blocks/ slices per stage")
                return
            pass
        self.numSlices = {}
        for mem in self.memoryTypes:
            if type(numSlices[mem]) == int:
                self.numSlices[mem] = numSlices[mem] * np.ones(numStages)
            else:
                self.numSlices[mem] = numSlices[mem]
                pass
            pass
        switchInfoStr += ("\nNumber of blocks: %s" %\
                         str([(mem, self.numSlices[mem][0]) for mem in\
                                  self.memoryTypes]))

        self.toposortOrderStages = toposortOrder
        if toposortOrder == []:
            self.toposortOrderStages = [st for st in range(numStages)]
            pass

        self.toposortOrderStages = self.toposortOrderStages
        
        switchInfoStr += ("\nTopo. sort for stages: %s " % self.toposortOrderStages)
        self.unpackableMemTypes = unpackableMemTypes
        self.numStages = numStages
        switchInfoStr += ("\nNumber of stages: %s " % self.numStages)

        self.depth = depth
        self.width = width
        switchInfoStr += ("\nDepth and width of memory: %s "\
                         % ["%dx%db %s" % (depth[mem], width[mem], mem)\
                                for mem in self.memoryTypes])

        self.inputCrossbarNumSubunits = inputCrossbarNumSubunits
        self.inputCrossbarWidthSubunit = inputCrossbarWidthSubunit
        switchInfoStr += ("\nInput crossbar: %s "\
                         % ["%d %db %s" % (inputCrossbarNumSubunits[mem],\
                                               inputCrossbarWidthSubunit[mem],\
                                               mem)\
                                for mem in self.memoryTypes])
        self.actionCrossbarNumBits = actionCrossbarNumBits
        switchInfoStr += ("\nAction crossbar has %d bits" % actionCrossbarNumBits)

        self.resolutionLogicNumMatchTables =\
            matchTablesPerStage['sram']
        switchInfoStr += ("\nMatch Tables per stage: %s" %\
                         ["%d %s" % (matchTablesPerStage[mem], mem) for\
                              mem in self.memoryTypes])

        self.matchDelay = delays['match']
        self.actionDelay = delays['action']
        self.successorDelay = delays['successor']
        switchInfoStr += ("\nPipeline delays: %s" % delays)

        self.power = power
        power['wattsPerTcam'] =\
            power['wattsPerTcamBit'] * self.width['tcam'] *\
            self.depth['tcam']
        power['wattsPerSram'] =\
            power['wattsPerSramBit'] * self.width['sram'] *\
            self.depth['sram']
        
        switchInfoStr += ("\nPower numbers: %s" % power)

        self.typesIn = {}
        self.typesIn['sram'] = ['sram', 'action']
        for mem in self.memoryTypes:
            if mem not in self.typesIn:
                self.typesIn[mem] = [mem]
                pass
            pass
        switchInfoStr += "\nTypes in: %s" % self.typesIn
        
        allTypes = {}
        self.inMem = {}
        for mem in self.memoryTypes:
            for thing in self.typesIn[mem]:
                self.inMem[thing] = mem
                if thing not in allTypes:
                    allTypes[thing] = 1
                    pass
                pass
            pass
        self.allTypes = sorted(allTypes.keys())
        switchInfoStr += "\nAll types: %s" % self.allTypes
        
        self.logger.info(switchInfoStr)
        pass

