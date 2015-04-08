import numpy as np
import logging

class RmtPreprocess:
    def __init__(self):
        # action memory per log. table
        # Want just adjacent blocks per log. table 
        # for tcam, sram, action, stats..
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
        return int(self.lcm(logicalWidth, blockWidth)/blockWidth)


    def setUseMemory(self):
        self.use = {}
        for mem in self.switch.memoryTypes:
            self.use[mem] = np.zeros(self.program.MaximumLogicalTables)
            pass
        
        for table in range(self.program.MaximumLogicalTables):
            for mem in self.switch.memoryTypes:
                tableType = self.program.matchType[table]
                switchTypes = self.switch.matchType[mem]
                self.logger.debug("table type %s in switchTypes? %s" % (tableType, str(switchTypes)))
                if  tableType in switchTypes:
                  self.use[mem][table] = 1
                  pass
                pass
        pass


    def preprocess(self, program, switch):
        logMax = program.MaximumLogicalTables
        self.program = program
        self.switch = switch
        self.setUseMemory()
        
        self.toposortOrderStages = switch.toposortOrderStages
        """
        SRAM packing factors
        - 32 bit overhead per logical word
        - logical word, overhead rounded up to 2^3 bits
        - string together so we can have >= 1 (logical word + overhead)/ row
        - 3-way hashing- 3 or 6 or 9 .. (logical word + overhead)/ row
        - could use min pf that satisfies these constraints
        - but bigger feasible pfs could save bits, let compiler optimize
        """

        allMaxPfs = max([self.getMaxPf(logicalWidth[0,0], switch.width['sram'])\
                             for logicalWidth in program.logicalTableWidths[:, 0]])
        pfMax = min(4, allMaxPfs)
        
        # Picking arbitrary packing factors
        self.layout = {}
        self.layout['sram'] = np.zeros((logMax, pfMax))

        self.word = {}
        self.word['sram'] = np.zeros((logMax, pfMax))

        for log in range(logMax):
            startPf = int(np.ceil(float(program.logicalTableWidths[log])/\
                              switch.inputCrossbarWidthSubunit['sram']))

            # Exactly one word per startPf RAMs
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
                pass
            pass

        """
        Additional blocks in SRAM
        - actionBlocks[log]: # sram blocks to store actions for log in st
        (if st is used, sram or tcam), decide how to pack etc. in preproc.
        - statsBlocks[log]: TODO(lav): same as actionBlocks?
        - tcamOverheadBlocks[log]: TODO(lav): we know # pf-blocks in stg,
        assume we'll fill all of them (actually not true for last pf-block)

        How many SRAM blocks do we need for its overhead?
        - we can fix action blocks per pf-block and multiply
        - or pack tighter, add an XTcamOverhead with capacity constraints
        and assignment constraints just that logical words in\
        XTcamOverhead[log, stg] is at least logical words in Xtcam[log, st].
        """

        
        # not optimizing, just fix pf per log. for TCAM for one entry per
        # pf-row. self.layoutTcam[0,log] is the number of blocks for the
        # smallest unit in the 0th layout for log

        for mem in self.switch.unpackableMemTypes:
            self.layout[mem] = np.matrix([np.ceil(float(m)/switch.width[mem]) for m in\
                                                 program.logicalTableWidths]).T
            self.word[mem] = np.ones(logMax) * switch.depth[mem]
            pass

        self.NumPackingFactors = pfMax
        self.inputCrossbarNumSubunits = {}
        for mem in switch.memoryTypes:
            self.inputCrossbarNumSubunits[mem] = \
                np.matrix([np.ceil(float(m)/switch.inputCrossbarWidthSubunit[mem]) for m in\
                               program.logicalTableWidths]).T
            pass

        
        self.actionCrossbarNumBits = \
            np.matrix([np.ceil(float(max(widths))) for widths in\
                                   program.logicalTableActionWidths]).T
    
        """
        Action Blocks
        Each Logical Table has an action data word for each match.
        Different matches may have action data words of different widths.
        We don't know beforehand though which width is used for a match,
        so we'll allocate enough memory in each stage to store one word of
        the maximum width, for every match word in the stage.
        When the compiler assigns action memory for a table in some stage,
        it assigns memory in units of ActionBuildingBlockSize[mem, log] mem blocks.
        Each unit has space for action words corresponding to ActionBuildingBlockWords[mem,log]
        match words.
        Also the pre-processor inputs the maximum action word width for the crossbar constraint.
        So .. the compiler doesn't have to know about multiple widths etc.
        It only has to choose enough action building blocks, given that each building block
        is enough for some number of match words.
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
                actionWordsPerRow = np.floor(float(numRamsForOneEntry*self.switch.width['sram'])\
                                                 /actionWidth)
                words = actionWordsPerRow * switch.depth['sram']
                pass
            self.word['action'][log] = words
            layouts.append(layout)
            actionWidths.append(actionWidth)
            pass
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
        lb = max(int(maxValue - div + 1), 1)
        ub = int(maxValue + 1)
        for i in range(lb, ub):
            if i%div == 0:
                return i
            pass
        return -1 * div
            
