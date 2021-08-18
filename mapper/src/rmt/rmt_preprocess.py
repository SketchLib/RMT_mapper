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

class RmtPreprocess:
    """
    Preprocessor module that precomputes information such as candidate packing units
    for compiler to use.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        pass

    def gcd(self, a, b):
        big = int(max(a,b))
        small = int(min(a,b))
        while small:
            big, small = small, big % small
            pass
        return big
        
    def lcm(self, a, b):
        gcd = self.gcd(a, b)
        product = a * b
        lcm = int(round(product/gcd))
        return lcm
    
    def getMaxPf(self, logicalWidth, blockWidth):
        """ minimum number of memory blocks needed for match entries to
        fit evenly in each row without wasting any bits. Any more blocks
        and we can view it as a combination of smaller packing units
        """
        
        return int(self.lcm(logicalWidth, blockWidth)/blockWidth)


    def setUseMemory(self):
        """ Based on table's match type e.g., exact/ ternary etc., determine
        which switch memory types it can use e.g., SRAM and TCAM/ TCAM etc.
        """
        self.use = {}
        for mem in self.switch.memoryTypes:
            self.use[mem] = np.zeros(self.program.MaximumLogicalTables)
            pass
        
        for table in range(self.program.MaximumLogicalTables):
            matchingMemTypeFound = False
            tableType = self.program.matchType[table]
            for mem in self.switch.memoryTypes:
                switchTypes = self.switch.matchType[mem]
                if  tableType in switchTypes:
                  matchingMemTypeFound = True
                  self.use[mem][table] = 1
                  pass
                pass
            if not matchingMemTypeFound:
                self.logger.error("Table match type (from program) " + tableType\
                                      + " doesn't match any switch memory type"\
                                      + " (from switch) "\
                                      + str(self.switch.matchType))
                exit()
                pass

            pass
        pass


    def preprocess(self, program, switch):
        logMax = program.MaximumLogicalTables
        self.program = program
        self.switch = switch
        self.setUseMemory()

        """
        Order in which stages execute, for RMT, stages execute
        one after another.
        """
        self.toposortOrderStages = switch.toposortOrderStages

        # print(program.logicalTableWidths)
        # print(switch.width['sram'])
        allMaxPfs = max([self.getMaxPf(logicalWidth[0,0], switch.width['sram']) for logicalWidth in program.logicalTableWidths[:, 0]])
        # print(allMaxPfs)
        # exit(1)
        """
        Limit packing unit size to 4 SRAM blocks
        """
        pfMax = min(4, allMaxPfs)
        # if pfMax == 0:
        #     pfMax = 1
        # layout['sram'](log, pf) is the number of RAMs
        # that make up the pfth packing unit for table log
        # and 'sram' memories
        self.layout = {}
        self.layout['sram'] = np.zeros((logMax, pfMax))

        # words['sram'](log, pf) is the number of match entries
        # per row of the pfth packing unit for table log
        # and 'sram' memories
        self.word = {}
        self.word['sram'] = np.zeros((logMax, pfMax))

        for log in range(logMax):
            startPf = int(np.ceil(float(program.logicalTableWidths[log])/switch.inputCrossbarWidthSubunit['sram']))

            # startPf is the number of RAMs to fit not more than one entry per Row
            # e.g., for a 128b wide entry and 80b RAMs, startPf is 2.
            # print(logMax)
            # print(log)
            # print(startPf)
            self.layout['sram'][log, 0] = startPf
            self.word['sram'][log, 0] = switch.depth['sram']

            
            # As many words as we can fit in xx RAMs, xx in [startPf, ..pfMax]
            # But if xx > getMaxPf(log), it's redundant- e.g., 128b word
            # in 128b RAM, a possible packing unit is 1K words in 1 RAM.
            # 2 RAMs is just 2 such packing units, it's not a new packing unit
            # set number of words to < 0, so compiler doesn't use this option.
            for pf in range(1, pfMax):
                numRams = startPf + pf - 1
                
                self.layout['sram'][log, pf] = numRams

                logicalWidth = program.logicalTableWidths[log]
                switchWidth = switch.width['sram']
                maxWords = \
                    (self.GetMultipleBefore(numRams*switchWidth,\
                                                logicalWidth)/logicalWidth)\
                                                * switch.depth['sram']
                # set number of words to < 0, so compiler doesn't use this option.
                if numRams > self.getMaxPf(logicalWidth[0,0], switch.width['sram']):
                    maxWords = -1
                    pass
                # set maxWords to 0, so LP compiler doesn't use this option
                maxWords = max(maxWords, 0)
                self.word['sram'][log, pf] = maxWords

        
        # No 'multiple entries per packing unit' for TCAMs and other 'unpackableMemTypes',
        # Only one possible packing unit- whose size/ layout is the number of blocks
        # needed to fit not more than one match entry per row.
        for mem in self.switch.unpackableMemTypes:
            self.layout[mem] = np.matrix([np.ceil(float(m)/switch.width[mem]) for m in program.logicalTableWidths]).T
            self.word[mem] = np.ones(logMax) * switch.depth[mem]

        self.NumPackingFactors = pfMax

        # A 128b wide match entry will need two whole 80b wide input crossbar subunits.
        self.inputCrossbarNumSubunits = {}
        for mem in switch.memoryTypes:
            self.inputCrossbarNumSubunits[mem] = np.matrix([np.ceil(float(m)/switch.inputCrossbarWidthSubunit[mem]) for m in program.logicalTableWidths]).T

        # Only one of the different action data words available will be
        # moved to the ALUs via the action crossbar, reserve
        # as many bits as needed by the widest action data entry.
        self.actionCrossbarNumBits =  np.matrix([np.ceil(float(max(widths))) for widths in program.logicalTableActionWidths]).T
    
        """
        Memories needed for Action Data
        Each Logical Table has an action data word for each match.
        Different matches may have action data words of different widths.

        We'll allocate enough (action) memory in each stage to store one action data word of
        the maximum width, for every match entry in the stage.

        Also the pre-processor inputs the maximum action word width for the crossbar constraint.
        So .. the compiler doesn't have to know about multiple widths etc.

        It only has to choose enough action packing units, given that each action packing units
        is enough for some number of match entries.
        """
        layouts = []
        actionWidths = []
        self.word['action'] = np.ones(logMax)
        for log in range(logMax):
            actionWidth = 0
            if len(self.program.logicalTableActionWidths[log]) > 0:
                actionWidth = max(self.program.logicalTableActionWidths[log])
                pass
            actionWordsPerRow = 0
            layout = 0
            words = 0
            if actionWidth > 0:
                numRamsForOneEntry = np.ceil(float(actionWidth)/self.switch.width['sram'])
                layout = numRamsForOneEntry
                actionWordsPerRow = np.floor(float(numRamsForOneEntry*self.switch.width['sram'])/actionWidth)
                words = actionWordsPerRow * switch.depth['sram']

            self.word['action'][log] = words
            layouts.append(layout)
            actionWidths.append(actionWidth)

        self.layout['action'] = np.matrix(layouts).T
        self.actionWidths = actionWidths
        self.logger.debug("action widths")
        self.logger.debug(actionWidths)
        self.logger.debug("action layout")
        self.logger.debug(self.layout['action'])
        self.logger.debug("action words")
        self.logger.debug(self.word['action'])
        

        return
    


    def GetMultipleBefore(self, maxValue, div):
        """ Get multiple of div just before maxValue """
        lb = max(int(maxValue - div + 1), 1)
        ub = int(maxValue + 1)
        for i in range(lb, ub):
            if i%div == 0:
                return i
            pass
        return -1 * div
            
