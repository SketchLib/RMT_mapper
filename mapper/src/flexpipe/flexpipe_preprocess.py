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
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        pass

    def slicesInStage(self, mem, st):
        startSlice = 0
        for stage in range(0,st):
            startSlice += self.switch.numSlices[mem][stage]
            pass
        
        return range(startSlice, startSlice + self.switch.numSlices[mem][st])

    def setUseMemory(self):
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
        self.toposortOrderStages = switch.order
        self.setUseMemory()
        for mem in switch.memoryTypes:
            self.pfBlocks[mem] = np.matrix([np.ceil(float(m)/switch.width[mem]) for m in\
                                        program.logicalTableWidths]).T
            pass
        return
    
        
