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



import logging
import numpy as np

class FlexpipePreprocess:
    """
    Preprocessor module that precomputes information such as valid packing units
    for compiler to use.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        pass

    def blocksInStage(self, mem, st):
        """ Returns indices of mem blocks in stage st
        Indexing starts from first mem block in the first
        stage and goes on till the last mem block over
        all stages.
        """
        startBlock = 0
        for stage in range(0,st):
            startBlock += self.switch.numBlocks[mem][stage]
            pass
        
        return range(startBlock, startBlock + self.switch.numBlocks[mem][st])

    def setUseMemory(self):
        """ Based on table's match type e.g., exact/ ternary etc., determine
        which switch memory types it can use e.g., SRAM and TCAM/ TCAM etc.
        """
        self.use = {}
        for mem in self.switch.memoryTypes:
            self.use[mem] = np.zeros(self.program.MaximumLogicalTables)
            pass
        
        for table in range(self.program.MaximumLogicalTables):
            for mem in self.switch.memoryTypes:
                if self.program.matchType[table] in\
                  self.switch.matchType[mem]:
                    self.use[mem][table] = 1
                    pass
                pass
        pass

    def preprocess(self, program, switch):
        self.switch = switch
        self.program = program
        self.pfBlocks = {}

        """
        Order in which stages execute, for FlexPipe as descibed
        in flexpipe_switch.py, stages execute one after another.
        """

        self.toposortOrderStages = switch.order
        self.setUseMemory()

        # pfBlocks[mem][log] is the number of RAMs
        # that make up a packing unit (that can fit one
        # entry per row) for table log and memories of type mem.

        for mem in switch.memoryTypes:
            self.pfBlocks[mem] = np.matrix([np.ceil(float(m)/switch.width[mem]) for m in\
                                        program.logicalTableWidths]).T
            pass
        return
    
        
