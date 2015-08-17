import logging
import numpy as np

"""
Intel FlexPipe switch.
"""

numSlices = {'mapper':[2,0,0,0],'ffu':[0,12,12,0], 'bst':[0,0,4,0],'hashtable':[0,0,0,4]}
order = [0,1,2,3]
maxTablesPerSlice = 4
depth = {'mapper':64, 'ffu':1000,'bst':16000, 'hashtable':16000}
width = {'mapper':48, 'ffu':36,'bst':36, 'hashtable':72}
class FlexpipeSwitch:
    def __init__(self, numSlices=numSlices, order=order, maxTablesPerSlice=maxTablesPerSlice, depth=depth, width=width):
        self.logger = logging.getLogger(__name__)

        memoryTypes = numSlices.keys()
        self.memoryTypes = memoryTypes
        self.numSlices = numSlices
        self.depth = depth
        self.order = order
        self.width = width
        self.numStages = max([len(numSlices[mem]) for mem in memoryTypes])
        self.maxTablesPerSlice = maxTablesPerSlice
        if len(order)==0:
            self.order = range(self.numStages)
            pass

        self.matchType = {}
        self.matchType['ffu'] = ['ternary','exact','lpm']
        self.matchType['hashtable'] = ['exact']
        self.matchType['bst'] = ['lpm','exact']
        self.matchType['mapper'] = ['mapper']
        
        pass
