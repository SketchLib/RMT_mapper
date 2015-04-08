import numpy as np

class FlexpipePreprocess:
    def __init__(self):
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
    
        
