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


class RmtSwitch:
    """
    RMT switch. Describes resources to be configured in the RMT switch.
    """

    
    def __init__(self,  numBlocks = {'sram':106, 'tcam':16},\
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
                     toposortOrder = [],
                     maxHashDistUnit=1000, # substitute_with_tofino_numbers
                     maxSALU=1000, # substitute_with_tofino_numbers
                     maxMapRAM=1000): # substitute_with_tofino_numbers

        """ initialize with resources available in each stage
        Stages in the RMT chip are uniform- i.e., they have
        the same distribution of resources- memory blocks,
        crossbar subunits, action crossbar bits etc.

        Thus @numBlocks is a mapping from memory types to a
        list of number of blocks, which applies for every stage.
        
        @depth and @width are mappings from memory types to the
        depth and width of inidividual blocks where-
         depth is the number of match entries the block can store
         width is the max. width of a match entry that can fit        

        @numStages is the number of stages
        
        @matchType is a mapping from memory types to the
         match types (exact, lpm etc.) that can be
         supported. E.g., sram supports "exact" match type
         but not "lpm" (longest prefix match).

         @inputCrossbarNumSubunits and @inputCrossbarWidthSubunit
        describe the input crossbars available
        for each of SRAMs and TCAMs in every stage. An input
        crossbar carries the fields to be matched from
        the packet header (vector) to the actual memories.
        It is made of subunits of fixed width. E.g., to match
        a 128b IPv6 address we would need 2 80b subunits.

        @actionCrossbar specifies the width of the action
        crossbar in each stage. There is one action crossbar
        that carries "inputs to table actions" (action data)
        from the SRAMs to the action ALUs. Note that
        action data is always stored in SRAMs, even if the corresponding
        match entries/ logical table is in TCAM.

        @matchTablesPerStage is the maximum number of different
        logical tables that can be supported per-stage per-memory
        types. This limit is a consequence of the fixed
        resolution logic per-stage that resolves table matches-
        the logic can support only a fixed number of tables.

        @delays[dep] is the number of cycles spent in a stage st
        when a table in stage st+1 has a dependency of type
        @dep on a table in stage st. E.g., when there is
        a match dependency where table in st+1 matches on
        a field modified by table in st, then st+1 wait
        for both match and action to complete in st, before
        it can start matching- this takes 12 cycles.

        @power is an estimate of the power used per memory type.

        @unpackableMemTypes is a list of memory types that
        don't support packing memory blocks together
        to support more than one match entry per row
        - they can be packed together to support only
        one match entry per row. E.g., two 40b wide
        TCAMs can be used to match a 60b field. But
        we can't pack three 40b TCAMs for two 60b
        fields.
        
        @topoSortOrder is a list indexed by stage number where @order[i]
         is the topological order of stage i in the
         execution graph (where nodes correspond to stages
         and there is an edge from stage x to y if y executes
         after x). E.g., in a pipeline where stage 3 and 4 execute simultaneously
         order[3] = order[4] etc. 
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info("RMT SWITCH")

        self.memoryTypes = sorted([k for k in depth])
        self.logger.info("Memory types: %s" % self.memoryTypes)

        self.matchType = matchType
        self.logger.info("Match type: %s" % self.matchType)

        for mem in self.memoryTypes:
            if type(numBlocks) == list and\
                    len(numBlocks[mem]) != numStages:
                self.logger.info("Invalid blocks per stage")
                return
            pass
        self.numBlocks = {}
        for mem in self.memoryTypes:
            if type(numBlocks[mem]) == int:
                self.numBlocks[mem] = numBlocks[mem] * np.ones(numStages)
            else:
                self.numBlocks[mem] = numBlocks[mem]
                pass
            pass
        self.logger.info("Number of blocks: %s" %\
                         str([(mem, self.numBlocks[mem][0]) for mem in\
                                  self.memoryTypes]))

        self.toposortOrderStages = toposortOrder
        if toposortOrder == []:
            self.toposortOrderStages = [st for st in range(numStages)]
            pass

        self.toposortOrderStages = self.toposortOrderStages
        
        #self.logger.info("Topo. sort for stages: %s " % self.toposortOrderStages)
        # can pack multiple TCAMs together to store only up to one match entry per row
        # not more, unlike SRAMs. So TCAM is "unpackable"
        self.unpackableMemTypes = unpackableMemTypes
        self.numStages = numStages
        self.logger.info("Number of stages: %s " % self.numStages)

        self.depth = depth
        self.width = width
        self.logger.info("Depth and width of memory: %s "\
                         % ["%dx%db %s" % (depth[mem], width[mem], mem)\
                                for mem in self.memoryTypes])

        self.inputCrossbarNumSubunits = inputCrossbarNumSubunits
        self.inputCrossbarWidthSubunit = inputCrossbarWidthSubunit
        self.logger.info("Input crossbar: %s "\
                         % ["%d %db %s" % (inputCrossbarNumSubunits[mem],\
                                               inputCrossbarWidthSubunit[mem],\
                                               mem)\
                                for mem in self.memoryTypes])
        self.actionCrossbarNumBits = actionCrossbarNumBits
        self.logger.info("Action crossbar has %d bits" % actionCrossbarNumBits)

        self.resolutionLogicNumMatchTables =\
            matchTablesPerStage['sram']
        self.logger.info("Match Tables per stage: %s" %\
                         ["%d %s" % (matchTablesPerStage[mem], mem) for\
                              mem in self.memoryTypes])

        self.matchDelay = delays['match']
        self.actionDelay = delays['action']
        self.successorDelay = delays['successor']
        self.logger.info("Pipeline delays: %s" % delays)

        self.power = power
        power['wattsPerTcam'] =\
            power['wattsPerTcamBit'] * self.width['tcam'] *\
            self.depth['tcam']
        power['wattsPerSram'] =\
            power['wattsPerSramBit'] * self.width['sram'] *\
            self.depth['sram']
        
        self.logger.info("Power numbers: %s" % power)

        # messy way to indicate type action data goes in SRAM
        # type SRAM match data (confusingly called sram) goes in SRAM
        # type TCAM match data (confusingly called tcam) goes in TCAM
        # and similiary for other memory types like SRAM, TCAM
        self.typesIn = {}
        self.typesIn['sram'] = ['sram', 'action']
        for mem in self.memoryTypes:
            if mem not in self.typesIn:
                self.typesIn[mem] = [mem]
                pass
            pass
        self.logger.info("Types in: %s" % self.typesIn)
        
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
        self.logger.info("All types: %s" % self.allTypes)
        
        self.logger.info("Hash Dist Unit per stage: %d" % maxHashDistUnit)
        self.maxHashDistUnit = maxHashDistUnit

        self.logger.info("SALU per stage: %d" % maxSALU)
        self.maxSALU = maxSALU

        self.logger.info("mapRAM: %d" % maxMapRAM)
        self.maxMapRAM = maxMapRAM


