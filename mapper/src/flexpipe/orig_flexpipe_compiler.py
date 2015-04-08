from pycpx import CPlexModel
import inspect
import flexpipe_lpt_compiler
from flexpipe_configuration import FlexpipeConfiguration
import numpy as np
from datetime import datetime
import time
import logging
"""
Assign number of blocks for each layout, compute number
of logical words from blocks.
"""
use_ilp = True # When False, solves LP.

class FlexpipeIlpCompiler:
    def __init__(self, relativeGap=None,\
                     epagap = None,\
                     greedyVersion = None,\
                     touches=False,\
                     emphasis=None,\
                     populateLimit = None,\
                     solnpoolintensity = None,\
                     treeLimit=None,\
                     timeLimit=None,\
                     variableSelect=None,\
                     workMem=None,\
                     nodeFileInd=None,\
                     workDir=None,\
                     outputFileName=None,\
                     writeLevel = None,\
                     mipstartFile = None,\
                     granMem = None):

        # Additional constraints for top-most
        self.touches = touches
        self.granMem = granMem

        self.emphasis = emphasis
        self.populateLimit = populateLimit
        self.solnpoolintensity = solnpoolintensity
        self.relativeGap = relativeGap
        self.epagap = epagap
        self.greedyVersion = greedyVersion
        self.treeLimit= treeLimit
        self.timeLimit = timeLimit
        self.variableSelect = variableSelect
    
        self.workMem = workMem
        self.nodeFileInd = nodeFileInd
        self.workDir = workDir
        logging.info("workDir: %s" % self.workDir)
        self.writeLevel = writeLevel
        self.mipstartFile = mipstartFile
        logging.info("mipstartFile: %s" % self.mipstartFile)
        self.outputFileName=outputFileName
        self.checking = False
        # allSl: maxslMax, sl: per mem per stage?,
        # slPerMem: all slices of mem across stages
        # slPerStage: all slices of stage across mem (use slicesInStage)
        self.dictNumVariables = \
            {'log': 0, 'st': 0, 'mem': 0, 'sl':0, 'log*st':0,
             'mem*log':0, 'mem*st':0, 'mem*log*st': 0,
             'log*sl':0, 'sl*ord':0, 'log*sl*ord':0,
             'constant': 0,
             'succDep':0, 'matchDep':0, 'actionDep':0
            }
        self.numVariables = 0
        self.dictNumConstraints = \
            {'log': 0, 'st': 0, 'mem': 0, 'sl':0, 'log*st':0,
             'mem*log':0, 'mem*st':0, 'mem*log*st': 0,
             'log*sl':0, 'sl*ord':0, 'log*sl*ord':0,
             'constant': 0,
             'succDep':0, 'matchDep':0, 'actionDep':0
            }
        self.numConstraints = 0
        self.testNumConstraints = 0
        self.dimensionSizes = {}
        # indexed by name
        self.variablesByName = {}
        self.variables = {}
        self.names = {}
        self.varUb = {}
        self.varLb = {}
        self.varType = {}

        self.gran = {}
        pass

    def iOSl(self, mem, order, sl):
        return order * self.totalSlMax[mem] + sl

    def iLSl(self, mem, log, sl):
        return log * self.totalSlMax[mem] + sl

    def iLSt(self, log, st):
        return log * self.stMax + st

    def iSlOL(self, mem, sl, order, log):
        numOrderLog = self.orderMax * self.logMax
        numLog = self.logMax
        
        return sl * self.orderMax * self.logMax +\
            order * self.logMax + log
    
    def setDimensionSizes(self):
        self.dimensionSizes = {
            'log': self.logMax, 
            'st': self.stMax, 
            'mem': len(self.switch.memoryTypes), 
            'sl': self.maxSlMax, 
            'log*st': self.logMax*self.stMax, 
            'mem*log': self.logMax*len(self.switch.memoryTypes),
            'mem*st':len(self.switch.memoryTypes)*self.stMax,
            'mem*log*st': len(self.switch.memoryTypes)*self.logMax*self.stMax,
            'log*sl': self.maxSlMax*self.logMax,
            'sl*ord': self.maxSlMax*self.orderMax,
            'log*sl*ord': self.logMax*self.maxSlMax*self.orderMax,
            'constant': 1,
            'succDep': len(self.program.logicalSuccessorDependencyList),
            'matchDep': len(self.program.logicalMatchDependencyList),
            'actionDep': len(self.program.logicalActionDependencyList)
        }
        pass

    def newVar(self, dims, vtype, name, ub=None, lb=None, realOkay=True):
        if realOkay and vtype == int:
            vtype='real'
            pass

        if vtype == bool:
            vtype = int
            ub = 1
            lb = 0
            pass
        
        try:
            assert(name not in self.variables)
        except AssertionError as e:
            e.args += (name, "length: ", len(self.variables))
            raise
        
        self.variablesByName[name] =\
            self.m.new(dims, vtype=vtype, name=name, ub=ub, lb=lb)
        # So we can parametrize vars (as coming from m or some other dict)
        # in all constraints.
        self.variables[self.variablesByName[name]] = self.variablesByName[name]
        self.names[self.variablesByName[name]] = name
        self.varUb[name] = ub
        self.varLb[name] = lb
        self.varType[name] = vtype
        return self.variablesByName[name]

    def newConstr(self, expr):
        # if self.checking = True, add violated constraint to self.violated
        if not self.checking:
            self.m.constrain(expr)
            pass
        else:
            valid = expr
            if not valid:
                stack = inspect.stack()
                val = [fun[3] for fun in stack[1:4]]
                if val not in self.violated:
                    self.violated.append(val)
                pass
            return valid
        pass

    def computeSum(self, dictCount):
        log_list = []
        compute_value = 0
        for key in dictCount:
            log_list.append('%d*%s(%d)' % \
                (dictCount[key], key, self.dimensionSizes[key]))
            compute_value += dictCount[key]*self.dimensionSizes[key]
        logging.info("%s = %d" % (" + ".join(log_list), compute_value))

        return compute_value

    def sliceOverlap(self, mem, sl1, log, sl2):
        if sl1 not in self.slicesInSameStageAs(mem, sl2):
            logging.debug("slice overlap, different stages: " + str(sl1) + ", " + str(sl2))
            pass
        return sl1 + self.preprocess.pfBlocks[mem][log] > sl2

    def slicesInStage(self, mem, st):
        startSlice = 0
        for stage in range(0,st):
            startSlice += self.slMax[mem][stage]
            pass
        
        return range(startSlice, startSlice + self.slMax[mem][st])
    
    def slicesInSameStageAs(self, mem, sl):
        """
        Returns list of slices for the stage (st) that sl is part of.
        ex: sl = 20, slices/st = 10 for all stages (sl indexed from 0).
        loop: sl=20->10, totalSlices=10; sl=10->0, totalSlices=20,
            sl=0->-10, totalSlices=30
        return: range(20-10, 20) = [10...19] (st: 0-9, 10-19, 20-29)
        (sl = 20, index 0 -> st=3; sl=20 (20...29), index 1 -> st=2 (11...20)

        """
        st = 0
        totalSlices = 0
        while(sl >= 0):
            slicesPerStage = self.slMax[mem][st]
            sl -= slicesPerStage
            totalSlices += slicesPerStage
            st += 1
            pass
        return range(totalSlices - slicesPerStage, totalSlices)

    def flattenOrdSl(self, d, mem):
        ordMax, slMax = d.shape
        maxIndex  = ordMax * slMax
        arr = np.zeros((maxIndex,1),dtype=np.int)
        # Logical Tables x Number Of Slices
        for order in range(ordMax):
            for sl in range(slMax):
                arr[self.iOSl(mem, order, sl)] =\
                  d[order, sl]
                pass
            pass
        return arr

    def flattenLogSl(self, d, mem):
        logMax, slMax = d.shape
        maxIndex  = logMax * slMax
        arr = np.zeros((maxIndex,1),dtype=np.int)
        # Logical Tables x Number Of Slices
        for log in range(logMax):
            for sl in range(slMax):
                arr[self.iLSl(mem, log, sl)] =\
                  d[log, sl]
                pass
            pass
        return arr

    def flattenLogSt(self, d, mem):
        logMax, stMax = d.shape
        maxIndex  = logMax * stMax
        arr = np.zeros((maxIndex,1), dtype=np.int)
        # Logical Tables x Number Of Slices
        for log in range(logMax):
            for st in range(stMax):
                arr[self.iLSt(log, st)] =\
                  d[log, st]
                pass
            pass
        return arr

    def getTouchesStartingDictValues(self, model):
        for mem in self.switch.memoryTypes:
            maxIndex = sum(self.slMax[mem]) * self.logMax
            maxIndexSlOL = sum(self.slMax[mem]) * self.logMax * self.orderMax
            model[self.firstRowOfTableBeforeIfOrd[mem]] = np.zeros((maxIndexSlOL), dtype=np.int)
            model[self.numberOfRowsOfTableBeforeIfOrd[mem]] = np.zeros((maxIndexSlOL), dtype=np.int)
            model[self.firstRowOfTableBefore[mem]] = np.zeros((maxIndex), dtype=np.int)
            model[self.numberOfRowsOfTableBefore[mem]] = np.zeros((maxIndex), dtype=np.int)
            model[self.numberOfRowsOfTableBeforeBinary[mem]] = np.zeros((maxIndex), dtype=np.int)
            model[self.firstRowOfTableMinusLastRowOfTableBeforeBinary[mem]] =\
                np.zeros((maxIndex), dtype=np.int)
            model[self.touchesTableBefore[mem]] = np.zeros((maxIndex), dtype=np.int)
            model[self.notFirstTableInAllSlicesBinary[mem]] = np.zeros((maxIndex), dtype=np.int)
            pass

        memXLogXSl = [(mem,log,sl)\
                          for mem in self.switch.memoryTypes\
                          for log in range(self.logMax)\
                          for sl in range(sum(self.slMax[mem]))]
        for mem,log,sl in memXLogXSl:
            totalFirstRow = 0
            totalNumberOfRows = 0

            for order in range(1,self.orderMax):
                prod =\
                    model[self.numberOfRowsOfOrd[mem]][self.iOSl(mem,order-1,sl)] *\
                    model[self.ordToLog[mem]][self.iSlOL(mem,sl,order,log)]
                model[self.numberOfRowsOfTableBeforeIfOrd[mem]][self.iSlOL(mem,sl,order,log)] = prod
                totalNumberOfRows += prod

                prod =\
                    model[self.firstRowOfOrd[mem]][self.iOSl(mem,order-1,sl)] *\
                    model[self.ordToLog[mem]][self.iSlOL(mem,sl,order,log)]
                model[self.firstRowOfTableBeforeIfOrd[mem]][self.iSlOL(mem,sl,order,log)] = prod
                totalFirstRow += prod            

                pass
            
            model[self.firstRowOfTableBefore[mem]][self.iLSl(mem,log,sl)] = totalFirstRow
            model[self.numberOfRowsOfTableBefore[mem]][self.iLSl(mem,log,sl)] = totalNumberOfRows
        
            ub = self.ub[mem]['numberOfRowsOfTableBefore']
            binary = 0
            if (round(model[self.numberOfRowsOfTableBefore[mem]][self.iLSl(mem,log,sl)]) > 0):
                binary = 1
                pass
            model[self.numberOfRowsOfTableBeforeBinary[mem]][self.iLSl(mem,log,sl)] = binary

            ub = self.ub[mem]['firstRowOfLog']
            cont = model[self.firstRowOfLog[mem]][self.iLSl(mem,log,sl)]\
                - model[self.numberOfRowsOfTableBefore[mem]][self.iLSl(mem,log,sl)]\
                - model[self.firstRowOfTableBefore[mem]][self.iLSl(mem,log,sl)]
            binary = 0
            if (round(cont) > 0):
                binary = 1
                pass
            model[self.firstRowOfTableMinusLastRowOfTableBeforeBinary[mem]][self.iLSl(mem,log,sl)] =\
                binary


            binary1 = model[self.numberOfRowsOfTableBeforeBinary[mem]][self.iLSl(mem,log,sl)]
            model[self.touchesTableBefore[mem]][self.iLSl(mem,log,sl)] = binary1 * binary
            pass

        for (mem,log,sl) in memXLogXSl:
            hasRows = model[self.numberOfRowsBinary[mem]][self.iLSl(mem,log,sl)]
            touches = 0
            firstTableInSl = 0
            pf = self.preprocess.pfBlocks[mem][log]
            for sl2 in range(sl, sl+pf):
                touches += model[self.touchesTableBefore[mem]][self.iLSl(mem,log,sl)]
                # If number of rows is 0, ordToLog can be 1?
                firstTableInSl += model[self.ordToLog[mem]][self.iSlOL(mem,sl,0,log)]
                pass

            cont = pf - firstTableInSl # > 0 if not first table in all slices
            binary = 0
            if round(cont) > 0:
                binary = 1
                pass
            model[self.notFirstTableInAllSlicesBinary[mem]][self.iLSl(mem,log,sl)] = binary
            # If not first table in all slices and has rows, then touch >= 1
            # If first table in all slices and has rows, 0 + 1 - 1 .. 0
            # If not first table but has no rows .. 1 + 0 - 1 .. 0
            # If first table . no rows .. 0 + 0 -
            pass

        pass

    def fillModel(self, startRowDict, numberOfRowsDict, model):
        for mem in self.switch.memoryTypes:
            logMax, slMax = startRowDict[mem].shape
            for log in range(logMax):
                for sl in range(slMax):
                    startRowDict[mem][log, sl] = round(startRowDict[mem][log,sl])
                    numberOfRowsDict[mem][log, sl] = round(numberOfRowsDict[mem][log,sl])
                    pass
                pass
            pass

        for mem in self.switch.memoryTypes:
            # Get Start Row and number Of Rows
            startRowUnit = np.zeros((self.logMax, sum(self.slMax[mem])), dtype=np.int)
            numberOfRowsUnit = np.zeros((self.logMax, sum(self.slMax[mem])), dtype=np.int)
            numberOfRowsBinary = np.zeros((self.logMax, sum(self.slMax[mem])), dtype=np.int)
            startRowTimesNumberOfRowsBinary = np.zeros((self.logMax, sum(self.slMax[mem])), dtype=np.int)
            for log in range(self.logMax):
                for sl1 in range(sum(self.slMax[mem])):
                    if self.gran[mem] == None:
                        gr = 1
                        pass
                    else:
                        gr = self.gran[mem]
                        pass
                    startRowUnit[log,sl1] = round(startRowDict[mem][log,sl1])/float(gr)
                    if numberOfRowsDict[mem][log,sl1] > 0:
                        numberOfRowsUnit[log,sl1] = round(numberOfRowsDict[mem][log,sl1])/float(gr)
                        numberOfRowsBinary[log,sl1] = 1
                        startRowTimesNumberOfRowsBinary[log,sl1] = startRowDict[mem][log,sl1]
                        pass
                    pass
                pass
            
            logging.debug("numberOfRowsDict[%s]: %s" % (mem, str(numberOfRowsDict[mem])))
            # Get first row and number of rows of log ..
            firstRowOfLog = np.zeros((self.logMax, sum(self.slMax[mem])), dtype=np.int)
            numberOfRowsOfLog = np.zeros((self.logMax, sum(self.slMax[mem])), dtype=np.int)
            numberOfRowsOfLogBinary = np.zeros((self.logMax, sum(self.slMax[mem])), dtype=np.int)
            for log in range(self.logMax):
                for sl1 in range(sum(self.slMax[mem])):
                    # Check it's 0 if not starting in slice
                    if numberOfRowsDict[mem][log,sl1] > 0:
                        startRow = startRowDict[mem][log, sl1] 
                        numRows = numberOfRowsDict[mem][log,sl1]
                        allSlices = [sl2 for sl2 in self.slicesInSameStageAs(mem,sl1)\
                                     if sl2 >= sl1 and\
                                     sl1 + self.preprocess.pfBlocks[mem][log] > sl2]
                        for sl2 in allSlices:
                            firstRowOfLog[log,sl2] = startRow
                            numberOfRowsOfLog[log,sl2] = numRows
                            if numRows > 0:
                                numberOfRowsOfLogBinary[log,sl2] = 1
                                pass
                            pass
                        pass
                    pass
                pass

            # Get first row of ord and number of rows of ord
            firstRowOfOrd = np.zeros((self.orderMax, sum(self.slMax[mem])), dtype=np.int)
            numberOfRowsOfOrd = np.zeros((self.orderMax, sum(self.slMax[mem])), dtype=np.int)
            numberOfRowsOfOrdBinary = np.zeros((self.orderMax, sum(self.slMax[mem])), dtype=np.int)
            maxIndex = sum(self.slMax[mem]) * self.orderMax * self.logMax
            ordToLog = np.zeros((maxIndex), dtype=np.int)
            numberOfRowsOfLogTimesOrdToLog = np.zeros((maxIndex), dtype=np.int)
            firstRowOfLogTimesOrdToLog = np.zeros((maxIndex), dtype=np.int)
            for sl1 in range(sum(self.slMax[mem])):
                logsInSl1 = [log for log in range(self.logMax)\
                             if round(numberOfRowsOfLog[log,sl1]) > 0]
                logsInSl1 = sorted(logsInSl1, key=lambda l: firstRowOfLog[l, sl1])

                logInfo = ", ".join(["%d) %s (%d..%d)" %\
                                         (i, self.program.names[logsInSl1[i]], firstRowOfLog[logsInSl1[i],sl1],\
                                              firstRowOfLog[logsInSl1[i],sl1]+\
                                              numberOfRowsOfLog[logsInSl1[i],sl1]) for\
                                        i in range(len(logsInSl1))])
                
                logging.info("Tables in slice %d of mem %s: %s" %\
                                 (sl1, mem, logInfo))
                                      
                logging.debug("number of logs in Sl %d of mem %s is %d" % (sl1, mem, len(logsInSl1)))
                logging.debug("shape of firstRowOfOrd is %s" % str(firstRowOfOrd.shape))
                logging.debug("shape of firstRowOfLog is %s" % str(firstRowOfLog.shape))
                if (len(logsInSl1) > self.orderMax):
                    logging.warn("too many tables in slice %d of mem %s (%d)- %s" %\
                                     (sl1,mem,len(logsInSl1),\
                                          [self.program.names[log] for log in logsInSl1]))
                    pass
                for order in range(len(logsInSl1)):
                    log = logsInSl1[order]
                    ordToLog[self.iSlOL(mem,sl1,order,log)] = 1
                    firstRowOfLogTimesOrdToLog[self.iSlOL(mem,sl1,order,log)] =\
                      firstRowOfLog[log,sl1]
                    numberOfRowsOfLogTimesOrdToLog[self.iSlOL(mem,sl1,order,log)] =\
                      numberOfRowsOfLog[log,sl1]
                    logging.debug("first row of %d th table in slice %d" % (order, sl1) +\
                                  " = first row of logical table %d i.e., %d " % (log, firstRowOfLog[log,sl1]))
                    firstRowOfOrd[order, sl1] = firstRowOfLog[log,sl1]
                    numberOfRowsOfOrd[order, sl1] = numberOfRowsOfLog[log,sl1]
                    if numberOfRowsOfOrd[order, sl1] > 0:
                        numberOfRowsOfOrdBinary[order, sl1] = 1
                        pass
                    pass
                pass

            # Get number of words and slices per stage per logical table
            word = np.zeros((self.logMax,self.stMax), dtype=np.int)
            slices = np.zeros((self.logMax,self.stMax), dtype=np.int)
            for log in range(self.logMax):
                for st in range(self.stMax):
                    for sl in self.slicesInStage(mem,st):
                        word[log,st] += numberOfRowsDict[mem][log,sl]
                        slices[log,st] += numberOfRowsOfLogBinary[log,sl]
                        pass
                    pass
                pass

            totalSlices = np.zeros((self.stMax), dtype=np.int)
            totalSlicesBinary = np.zeros((self.stMax), dtype=np.int)
            for st in range(self.stMax):
                totalSlices[st] = sum([slices[log,st] for log in range(self.logMax)])
                if totalSlices[st] > 0:
                    totalSlicesBinary[st] = 1
                    pass
                pass

            model[self.startRow[mem]] =\
               self.flattenLogSl(startRowDict[mem], mem)
            model[self.startRowUnit[mem]] =\
               self.flattenLogSl(startRowUnit, mem)

            model[self.numberOfRows[mem]] =\
               self.flattenLogSl(numberOfRowsDict[mem], mem)
            model[self.numberOfRowsUnit[mem]] =\
               self.flattenLogSl(numberOfRowsUnit, mem)

            model[self.numberOfRowsBinary[mem]] =\
               self.flattenLogSl(numberOfRowsBinary, mem)
            model[self.startRowTimesNumberOfRowsBinary[mem]] =\
               self.flattenLogSl(startRowTimesNumberOfRowsBinary, mem)

            flatNumberOfRowsOfLog = self.flattenLogSl(numberOfRowsOfLog, mem) 
            model[self.firstRowOfLog[mem]] =\
              self.flattenLogSl(firstRowOfLog, mem)
            model[self.numberOfRowsOfLog[mem]] =\
              flatNumberOfRowsOfLog
            model[self.numberOfRowsOfLogBinary[mem]] =\
              self.flattenLogSl(numberOfRowsOfLogBinary, mem)

            #self.checkMaxTablesPerSliceConstraint(mem, flatNumberOfRowsOfLog)
            flatFirstRowOfOrd = self.flattenOrdSl(firstRowOfOrd, mem)
            flatNumberOfRowsOfOrd = self.flattenOrdSl(numberOfRowsOfOrd, mem) 
            flatNumberOfRowsOfOrdBinary = self.flattenOrdSl(numberOfRowsOfOrdBinary, mem)
            model[self.firstRowOfOrd[mem]] =\
              flatFirstRowOfOrd
            model[self.numberOfRowsOfOrd[mem]] =\
              flatNumberOfRowsOfOrd
            model[self.numberOfRowsOfOrdBinary[mem]] =\
              flatNumberOfRowsOfOrdBinary

            #self.checkOverlapConstraints(mem, flatFirstRowOfOrd, flatNumberOfRowsOfOrd,\
            #                             flatNumberOfRowsOfOrdBinary)

            model[self.ordToLog[mem]] =\
              ordToLog  
            model[self.firstRowOfLogTimesOrdToLog[mem]] =\
              firstRowOfLogTimesOrdToLog 
            model[self.numberOfRowsOfLogTimesOrdToLog[mem]] =\
              numberOfRowsOfLogTimesOrdToLog 

            model[self.word[mem]] =\
              self.flattenLogSt(word, mem)
            model[self.slices[mem]] =\
              self.flattenLogSt(slices, mem)
            #self.checkUseMemoryConstraint(model[self.slices[mem]], mem)

            model[self.totalSlices[mem]] =\
              totalSlices
            model[self.totalSlicesBinary[mem]] =\
              totalSlicesBinary      
            pass

        wordDict = {}
        for mem in self.switch.memoryTypes:
            wordDict[mem] = model[self.word[mem]]
            pass
        #self.checkAssignmentConstraint(wordDict)
        
        blockAllMemBin = np.zeros((self.logMax, self.stMax), dtype=np.int)
        startAllMem = np.zeros((self.logMax, self.stMax), dtype=np.int)
        endAllMem = np.zeros((self.logMax, self.stMax), dtype=np.int)
        startAllMemTimesBlockAllMemBin = np.zeros((self.logMax, self.stMax), dtype=np.int)
        endAllMemTimesBlockAllMemBin = np.zeros((self.logMax, self.stMax), dtype=np.int)

        for log in range(self.logMax):
            stages = [st for st in range(self.stMax)\
                      if any([numberOfRowsDict[mem][log,sl] > 0\
                              for mem in self.switch.memoryTypes\
                              for sl in self.slicesInStage(mem, st)])]
            if len(stages) == 0:
                logging.warn("Warning! " + str(log) + " not assigned to any stage")
                pass
            else:
                for st in stages:
                    blockAllMemBin[log,st] = 1
                    pass
                startAllMem[log,int(min(stages))] = 1
                endAllMem[log,int(max(stages))] = 1
                pass
            pass
        for log in range(self.logMax):
            for st in range(self.stMax):
                startAllMemTimesBlockAllMemBin[log,st] = startAllMem[log,st] *\
                    blockAllMemBin[log,st]
                endAllMemTimesBlockAllMemBin[log,st] = endAllMem[log,st] *\
                    blockAllMemBin[log,st]
                pass
            pass
        # mem not used here in flattenLogSt
        model[self.blockAllMemBin] = self.flattenLogSt(blockAllMemBin, mem)
        model[self.startAllMem] = self.flattenLogSt(startAllMem, mem)
        model[self.startAllMemTimesBlockAllMemBin] = self.flattenLogSt(\
            startAllMemTimesBlockAllMemBin, mem)
        model[self.endAllMem] = self.flattenLogSt(endAllMem, mem)
        model[self.endAllMemTimesBlockAllMemBin] = self.flattenLogSt(\
            endAllMemTimesBlockAllMemBin, mem)
        #self.checkDependencyConstraint(model[self.startAllMem], model[self.endAllMem])
        logging.info("initialized % d variables of ILP" % len(model.keys()))
        notInNames = [self.names[key] for key in self.names if key not in model]
        logging.info("Didn't initialize [%s]" % ", ".join(notInNames))

        pass

    def setup(self, program, switch, preprocess):
        self.setupVariables(program, switch, preprocess)
        self.setupStartAndEndStagesVariables()

        if self.touches:
            self.setupTouchesTableBeforeVariables()
            pass
        self.setupConstraints(model=self.variables)

        self.setupStartingDict()
        pass

    def setupVariables(self, program, switch, preprocess):
        self.program = program
        self.switch = switch
        self.preprocess = preprocess

        ####################################################
        # Constants
        ####################################################

        # Each stage has some slices for each kind of memory.
        # e.g., St 0 has 12 slices of FFU, St 1 has 12 slices of FFU, 4 of BST
        # Then ['FFU'][0..11] are slices in St 0, ['FFU'][12..23] in St 1
        # ['BST'][0..3] are slices in St 1 etc.
        # Can use switch.numSlices[mem][st] to figure out index.

        gran = {}
        for mem in switch.memoryTypes:
            if mem == 'mapper':
                gran[mem] = 32
                pass
            else:
                gran[mem] = self.granMem
                pass
            pass

        stMax = switch.numStages
        logMax = program.MaximumLogicalTables
        
        # upper bound on slices for a table in a stage
        slMax = {}
        totalSlMax = {}
        rowMax = {}
        for mem in self.switch.memoryTypes:
            rowMax[mem] = switch.depth[mem]
            # total slices of this mem in each stage
            slMax[mem] = switch.numSlices[mem]
            # sum of all slices for this mem in all stages
            totalSlMax[mem] = sum([slMax[mem][st] for st in range(stMax)])
            pass

        # sum of all slices(blocks) across all memories in all stages
        maxSlMax = int(sum([slMax[mem][st] for mem in slMax for st in range(stMax)]))

        # upper bound on logical words for a table in a stage
        # TODO: Is bound too high for wordMax?
        mem = switch.memoryTypes[0]
        wordMax = int(switch.depth[mem] * maxSlMax)        
        
        # Each slice can have up to orderMax tables, could depend on mem, st.
        orderMax = self.switch.maxTablesPerSlice
        logging.debug("orderMax: " + str(orderMax))
        self.gran = gran
        self.orderMax = orderMax
        self.stMax = stMax
        self.slMax = slMax
        self.totalSlMax = totalSlMax
        self.logMax = logMax
        self.rowMax = rowMax
        self.maxSlMax = maxSlMax
        self.wordMax = wordMax

        self.setDimensionSizes()
        ####################################################
        # Variables
        ####################################################
        self.results = {}

        self.results['relativeGap'] = self.relativeGap
        self.results['greedyVersion'] = self.greedyVersion
        self.results['stMax'] = switch.numStages

        self.m = CPlexModel(verbosity=3)


        # number of words for each logical table in each stage
        self.word = {}

        # number of slices for each logical table in each stage
        self.slices = {}

        # number of slices used in each stage
        self.totalSlices = {}
        self.totalSlicesBinary = {}

        # index of first row of rows for a logical table starting in a slice
        # 0/ not defined if logical table does not start in the slice.
        self.startRow = {}
        self.startRowUnit = {}
        self.numberOfRows = {}
        self.numberOfRowsUnit = {}
        self.numberOfRowsBinary = {}
        self.startRowTimesNumberOfRowsBinary = {}
        # index of first row of rows for a logical table in a slice
        # 0/ not defined if logical tables is not in the slices.
        self.firstRowOfLog = {}
        self.numberOfRowsOfLog = {}
        self.numberOfRowsOfLogBinary = {}

        # index of first row of ord'th tables in a slice
        self.firstRowOfOrd = {}
        self.numberOfRowsOfOrd = {}
        self.numberOfRowsOfOrdBinary = {}

        # 1 if ord'th table of slice is used for logical table.
        self.ordToLog = {}

        # first row of ord'th table of a slice, if assigned.
        # otherwise, 0.
        self.firstRowOfLogTimesOrdToLog = {}
        self.numberOfRowsOfLogTimesOrdToLog = {}
        ub = {}
        lb = {}
        self.dictNumVariables['mem*log*st'] += 1 # word
        self.dictNumVariables['mem*log*st'] += 1 # slices
        self.dictNumVariables['mem*st'] += 2 # slices
        self.dictNumVariables['log*sl'] += 2 # numberOfRows, binary
        self.dictNumVariables['log*sl'] += 2 # startRow, xNumberOfRowsBinary
        self.dictNumVariables['log*sl'] += 3 # firstRow, numberOfRows of Log, Binary
        self.dictNumVariables['log*sl*ord'] += 1 # ordToLog
        self.dictNumVariables['log*sl*ord'] += 2 # first/number RowTimesOrdToLog
        self.dictNumVariables['sl*ord'] += 3 # first/number RowTimesOrd, numberBinary
        testlist = []
        for mem in self.switch.memoryTypes:
            ub[mem] = {}
            lb[mem] = {}
            temptestlist = []
            
            numRowsMax = rowMax[mem]
            startRowMin = 0
            startRowMax = rowMax[mem]-1

            maxIndex = logMax * stMax
            vname='word'
            ub[mem][vname]= int(sum([slMax[mem][st] for st in range(stMax)])) * rowMax[mem]
            lb[mem][vname]=0            
            self.word[mem] = self.newVar((maxIndex), vtype=int,\
                                             lb=lb[mem][vname], ub=ub[mem][vname],\
                                             name=vname+mem, realOkay=True)
            vname='slices'
            ub[mem][vname]= int(sum([slMax[mem][st] for st in range(stMax)]))
            lb[mem][vname]=0            
            self.slices[mem] = self.newVar((maxIndex), vtype=int,\
                                               lb=lb[mem][vname], ub=ub[mem][vname],\
                                               name=vname+mem)

            maxIndex = stMax
            vname = 'totalSlices'
            ub[mem][vname]=ub[mem]['slices']*logMax
            lb[mem][vname]=0            
            self.totalSlices[mem] =\
                self.newVar((maxIndex), vtype=int,\
                                lb=lb[mem][vname], ub=ub[mem][vname],\
                                name=vname+mem)
            self.totalSlicesBinary[mem] =\
                self.newVar((maxIndex), vtype=bool,\
                                name='totalSlicesBinary'+mem)

            maxIndex = sum(slMax[mem])  * logMax
            vname = 'numberOfRows'
            ub[mem][vname]=rowMax[mem]
            lb[mem][vname]=0            
            self.numberOfRows[mem] = self.newVar((maxIndex),vtype=int,\
                                                     lb=lb[mem][vname], ub=ub[mem][vname],\
                                                     name=vname+mem)

            vname = 'numberOfRowsUnit'
            ub[mem][vname]=rowMax[mem]
            lb[mem][vname]=0            
            self.numberOfRowsUnit[mem] = self.newVar((maxIndex),vtype=int,\
                                                     lb=lb[mem][vname], ub=ub[mem][vname],\
                                                     name=vname+mem)


            self.numberOfRowsBinary[mem] =\
                self.newVar((maxIndex),vtype=bool,\
                                name='numberOfRowsBinary'+ mem)


            vname = 'startRow'
            ub[mem][vname]=rowMax[mem]
            lb[mem][vname]=0           

            self.startRow[mem] = self.newVar((maxIndex),vtype=int,\
                                                 lb=lb[mem][vname], ub=ub[mem][vname],\
                                                 name=vname+mem)

            vname = 'startRowUnit'
            ub[mem][vname]=rowMax[mem]
            lb[mem][vname]=0           

            self.startRowUnit[mem] = self.newVar((maxIndex),vtype=int,\
                                                 lb=lb[mem][vname], ub=ub[mem][vname],\
                                                 name=vname+mem)

            vname = 'startRowTimesNumberOfRowsBinary'
            ub[mem][vname]=rowMax[mem]
            lb[mem][vname]=0
            self.startRowTimesNumberOfRowsBinary[mem] = self.newVar((maxIndex),vtype=int,\
                                                                        lb=lb[mem][vname], ub=ub[mem][vname],\
                                                                        name=vname+mem, realOkay=True)
            
            vname = 'firstRowOfLog'
            ub[mem][vname]=rowMax[mem]
            lb[mem][vname]=0
            # sum over startRowTimesNumberOfRowsBinary * 1 if sl overlaps sl 1 for sl1 in same stage as sl
            self.firstRowOfLog[mem] = self.newVar((maxIndex),vtype=int,\
                                                      lb=lb[mem][vname], ub=ub[mem][vname],\
                                                      name=vname+mem, realOkay=True)


            vname = 'numberOfRowsOfLog'
            ub[mem][vname]=rowMax[mem]
            lb[mem][vname]=0
            # ditto as above, can be real (and would be int when it satisfies constraint)
            self.numberOfRowsOfLog[mem] = self.newVar((maxIndex),vtype=int,\
                                                          lb=lb[mem][vname], ub=ub[mem][vname],\
                                                          name=vname+mem, realOkay=True)
            self.numberOfRowsOfLogBinary[mem] =\
                self.newVar((maxIndex), vtype=bool,\
                                name='numberOfRowsOfLogBinary'+ mem)

            maxIndex = sum(slMax[mem]) * orderMax * logMax
            self.ordToLog[mem] = self.newVar((maxIndex),vtype=bool,\
                                                 name='ordToLog'+mem)
            vname = 'firstRowOfLogTimesOrdToLog'
            ub[mem][vname]=rowMax[mem]
            lb[mem][vname]=0
            self.firstRowOfLogTimesOrdToLog[mem] =\
                self.newVar((maxIndex),vtype=int,\
                                lb=lb[mem][vname], ub=ub[mem][vname],\
                                name=vname+mem, realOkay=True)

            vname = 'numberOfRowsOfLogTimesOrdToLog'
            ub[mem][vname]=rowMax[mem]
            lb[mem][vname]=0
            self.numberOfRowsOfLogTimesOrdToLog[mem] =\
                self.newVar((maxIndex),vtype=int,\
                                lb=lb[mem][vname], ub=ub[mem][vname],\
                                name=vname+mem, realOkay=True)

            maxIndex = sum(slMax[mem]) * orderMax
            vname = 'firstRowOfOrd'
            ub[mem][vname]=rowMax[mem]
            lb[mem][vname]=0
            # sum of firstRowOfLogTimesOrdToLog, already int
            self.firstRowOfOrd[mem] = self.newVar((maxIndex),vtype=int,\
                                                      lb=lb[mem][vname], ub=ub[mem][vname],\
                                                      name=vname+mem, realOkay=True)
            vname = 'numberOfRowsOfOrd'
            ub[mem][vname]=rowMax[mem]
            lb[mem][vname]=0
            self.numberOfRowsOfOrd[mem] = self.newVar((maxIndex),vtype=int,\
                                                          lb=lb[mem][vname], ub=ub[mem][vname],\
                                                          name=vname+mem, realOkay=True)

            self.numberOfRowsOfOrdBinary[mem] =\
                self.newVar((maxIndex),vtype=bool,\
                                name='numberOfRowsOfOrdBinary'+mem)
            pass

        
        # Maximum stage variables stMax * 2
        # Starting and ending stage variables logMax * stMax * 3 * 2
        maxIndex = logMax * stMax
        self.blockAllMemBin = self.newVar((maxIndex), vtype=bool, name='blockAllMemBin')

        self.dictNumVariables['log*st'] += 1 # blockAllMemBin
        self.ub = ub
        self.lb = lb
        pass


    def setupConstraints(self, model=None):
        switch = self.switch
        program = self.program
        preprocess = self.preprocess
        stMax = self.stMax
        logMax = self.logMax
        orderMax = self.orderMax
        ####################################################
        # Constraints
        ####################################################
        # Assign IP to 'ffu' and Ethertype to 'bst'
#        eps = 0.01
#        mem = 'ffu'
#        index = self.iSlOL('ffu', 1, 0, 1)
#        self.newConstr(self.numberOfRowsOfLogTimesOrdToLog[mem][index] >= eps)
#        mem = 'bst'
#        index = self.iSlOL('bst', 0, 0, 0)
#        self.newConstr(self.numberOfRowsOfLogTimesOrdToLog[mem][index] >= eps)
        
        # GET VARIABLES THAT DEPEND ON startRow, numberOfRows, ordToLog
       
        self.setupConstraintsForProductsAndBinarys(model=model)
        if self.touches:
            self.setupTouchesTableBeforeConstraints(model=model)
            pass

        self.getStartingAndEndingStages(model=model) # tested
        
        if self.granMem == None:
            logging.info("No granularity of row contraints")
            pass
        else:
            logging.info("Granularity 32 for mapper, %s for other" % self.granMem)
            self.startRowMultipleConstraint(model=model)
            pass

        # Get slices and words from numberOfRows variables
        self.wordLayoutConstraint(model=model)

        # Get totalSlices from slices variables
        for mem in switch.memoryTypes:
            for st in range(self.stMax):
                self.newConstr(model[self.totalSlices[mem]][st] ==\
                                   sum([model[self.slices[mem]][self.iLSt(log, st)]\
                                            for log in range(self.logMax)]))
                pass
            pass

        self.dictNumConstraints['mem*st'] += 1
        
        # ORDER CONSTRAINTS
        # A logical table assignment that overlaps a slice
        # is assigned to exactly one order in the slice.

        memXSl = [(mem,sl)\
                          for mem in self.switch.memoryTypes\
                          for st in range(self.stMax)\
                          for sl in self.slicesInStage(mem,st)]
        for mem,sl in memXSl:
            for log in range(self.logMax):
                self.getXXOfLog(mem=mem, sl=sl, log=log, model=model)
                self.oneOrderPerLogConstraint(mem=mem, sl=sl, log=log, model=model)
                self.capacityConstraintBySlice(mem=mem, log=log, sl=sl, model=model)
                pass
            for order in range(self.orderMax-1):
                self.getXXOfOrd(model=model, mem=mem, order=order, sl=sl)
                self.overlapConstraint(mem=mem, order=order, sl=sl, model=model)
                pass
            self.getXXOfOrd(model=model, mem=mem, order=self.orderMax-1, sl=sl)

            self.capacityConstraintByRow(mem, sl, model=model)
            self.maximumTablesPerSliceConstraint(mem,sl, model=model)
            pass
        
        # Assign enough match words for each table
        self.assignmentConstraint(model=model)

        # Match, Action, Successor dependency constraint on starting and 
        # ending stages for each logical table
        self.dependencyConstraint(model=model)


        # Use TCAM/ SRAM only where allowed
        self.useMemoryConstraint(model=model)
        pass

    def startRowMultipleConstraint(self, model=None):
        memXSl = [(mem,sl) for mem in self.switch.memoryTypes\
                      for st in range(self.stMax)\
                      for sl in self.slicesInStage(mem,st)]
        for mem,sl in memXSl:
            for log in range(self.logMax):
                index = self.iLSl(mem,log,sl)

                valid = self.newConstr(model[self.startRow[mem]][index]\
                                     == model[self.startRowUnit[mem]][index]\
                                     * self.gran[mem])

                if self.checking and not valid:
                    logging.info("start row [%s] [log=%s, sl=%d] is %d, startRow Unit is %d" %\
                                     (mem, self.program.names[log], sl, model[self.startRow[mem]][index],\
                                          model[self.startRowUnit[mem]][index]))
                    pass


                valid = self.newConstr(model[self.numberOfRows[mem]][index]\
                                     == model[self.numberOfRowsUnit[mem]][index]\
                                     * self.gran[mem])

                if self.checking and not valid:
                    logging.info("numberOfRows [%s] [log=%s, sl=%d] is %d, numberOfRowsUnit is %d" %\
                                     (mem, self.program.names[log], sl, model[self.numberOfRows[mem]][index],\
                                          model[self.numberOfRowsUnit[mem]][index]))
                    pass

                pass
            pass
        pass

    def setupStartingDict(self):
        self.startingDict = {}
        
        logging.debug("Solving " )
        self.configs = {}
        if not(self.greedyVersion == None) and len(self.greedyVersion)>0:
            ####################################################
            logging.info("Getting a greedy solution")
            greedyCompiler = flexpipe_lpt_compiler.FlexpipeLptCompiler()
            start = time.time()
            greedyConfig = greedyCompiler.solve(\
                self.program, self.switch, self.preprocess)['greedyConfig']
            self.configs['greedyConfig'] = greedyConfig
            end = time.time()
            ####################################################
            logging.debug("Saving results from greedy")
            self.results['greedyTime'] = end - start
            self.results['greedySolved'] = greedyCompiler.results['solved']
            ####################################################
            """
            if len(picPrefix) > 0:
                greedyConfig.showPic(prefix=picPrefix,suffix=picName+"-lpt")
            """
            ####################################################
            logging.debug("Getting starting dict values for ILP from Greedy's solution")
            self.startingDict = {}
            self.fillModel(greedyCompiler.startRowDict,\
                               greedyCompiler.numberOfRowsDict,\
                               self.startingDict)
            if self.touches:
                self.getTouchesStartingDictValues(model=self.startingDict)
                pass
            logging.info("Checking greedy's solution")
            self.checkSolution(model=self.startingDict)

            for mem in self.switch.memoryTypes:
                order = 0
                self.results['greedyUsedSlices'+mem] =\
                    greedyCompiler.results['usedSlices'+mem]
                pass
            self.results['greedyTotalUsedSlices'] =\
                greedyCompiler.results['totalUsedSlices']
                
            pass

        logging.info("results[Greedy .." + str(self.results))

        if 'greedySolved' in self.results and not self.results['greedySolved']:
            logging.warn("Greedy couldn't fit: " + str(self.results))
            pass
        
        return

    def checkSolution(self, model=None):
            self.checking = True
            self.violated = []
            self.setupConstraints(model=model)

            logging.info("Number of violated constraints: %d (%s...)" %\
                (len(self.violated), self.violated[:4]))
            

            outOfBounds = []
            for var in model:
                name = self.names[var]
                w,h = var.shape
                vals = model[var]
                moreThanUb = [(index,vals[index]) for index in range(w) if self.varUb[name] < vals[index]]
                lessThanLb = [(index,vals[index]) for index in range(w) if self.varLb[name] > vals[index]]
                infoStr = "%s: %s, %d more than UB (%d) [%s..], %d less than LB (%d) [%s..]" %\
                    (name, str(var.shape), len(moreThanUb), self.varUb[name],\
                         moreThanUb[:3], len(lessThanLb), self.varLb[name],\
                         lessThanLb[:3])
                if len(moreThanUb) > 0 or len(lessThanLb) > 0:
                    outOfBounds.append(infoStr)
                    pass
                pass
            logging.info("Number of out of bound variables: %d (%s...)" %\
                (len(outOfBounds), outOfBounds[:3]))

            self.checking = False
            pass

    def setupConstraintsForProductsAndBinarys(self, model=None):
        for st in range(self.stMax):
            # totalSlicesBinary
            for mem in self.switch.memoryTypes:
                cont = model[self.totalSlices[mem]][st]
                binary = model[self.totalSlicesBinary[mem]][st]
                ub = self.varUb['totalSlices'+mem]
                self.addBinaryConstraint(cont=cont,binary=binary,ub=ub)
                pass

            for log in range(self.logMax):
                index = self.iLSt(log,st)

                # BlockAllMemBin
                cont = sum([model[self.slices[mem]][index] for mem in self.switch.memoryTypes])
                binary = model[self.blockAllMemBin][index]
                ub = sum([self.varUb['slices'+mem] for mem in self.switch.memoryTypes])
                self.addBinaryConstraint(binary=binary, cont=cont, ub=ub)

                # XXAllMemTimesBlockAllMemBin
                prod = model[self.startAllMemTimesBlockAllMemBin][index]
                binary1 = model[self.startAllMemTimesBlockAllMemBin][index]
                binary2 = model[self.blockAllMemBin][index]
                self.addProductBinaryConstraint(prod=prod,binary1=binary1,binary2=binary2)

                prod = model[self.endAllMemTimesBlockAllMemBin][index]
                binary1 = model[self.endAllMemTimesBlockAllMemBin][index]
                binary2 = model[self.blockAllMemBin][index]
                self.addProductBinaryConstraint(prod=prod,binary1=binary1,binary2=binary2)

                pass
            pass

        memXSl = [(mem,sl) for mem in self.switch.memoryTypes\
                          for st in range(self.stMax)\
                          for sl in self.slicesInStage(mem,st)]
        for mem,sl in memXSl:
            for log in range(self.logMax):
                index = self.iLSl(mem,log,sl)
                # numberOfRowsOfLogBinary
                binary = model[self.numberOfRowsOfLogBinary[mem]][index]
                cont = model[self.numberOfRowsOfLog[mem]][index]
                ub = self.varUb['numberOfRowsOfLog'+mem]
                self.addBinaryConstraint(binary=binary,cont=cont,ub=ub)

                # numberOfRowsBinary
                binary = model[self.numberOfRowsBinary[mem]][index]
                cont = model[self.numberOfRows[mem]][index]
                ub = self.varUb['numberOfRows'+mem]
                self.addBinaryConstraint(binary=binary,cont=cont,ub=ub)

                # startRowTimesNumberOfRowsBinary
                prod = model[self.startRowTimesNumberOfRowsBinary[mem]][index]
                binary = model[self.numberOfRowsBinary[mem]][index] 
                cont = model[self.startRow[mem]][index]
                ub = self.varUb['startRow'+mem]
                self.addProductConstraint(prod=prod,cont=cont,binary=binary,ub=ub)

                # firstRowOfLogTimesOrdToLog
                cont = model[self.firstRowOfLog[mem]][index]
                ub = self.varUb['firstRowOfLog'+mem]
                for order in range(self.orderMax):
                    oIndex = self.iSlOL(mem, sl, order, log)
                    prod = model[self.firstRowOfLogTimesOrdToLog[mem]][oIndex]
                    binary = model[self.ordToLog[mem]][oIndex]
                    self.addProductConstraint(prod=prod, binary=binary, ub=ub, cont=cont)
                    pass

                # numberOfRowsOfLogTimesOrdToLog
                cont = model[self.numberOfRowsOfLog[mem]][index]
                ub = self.varUb['numberOfRowsOfLog'+mem]
                for order in range(self.orderMax):
                    oIndex = self.iSlOL(mem, sl, order, log)
                    prod = model[self.numberOfRowsOfLogTimesOrdToLog[mem]][oIndex]
                    binary = model[self.ordToLog[mem]][oIndex]
                    self.addProductConstraint(prod=prod, binary=binary, ub=ub, cont=cont)
                    pass

                pass

            for order in range(self.orderMax):
                # numberOfRowsOfOrdBinary
                index = self.iOSl(mem,order,sl)
                binary = model[self.numberOfRowsOfOrdBinary[mem]][index]
                cont = model[self.numberOfRowsOfOrd[mem]][index]
                ub = self.varUb['numberOfRowsOfOrd'+mem]
                self.addBinaryConstraint(binary=binary,cont=cont,ub=ub)
                pass
            pass


        pass

    def setupStartAndEndStagesVariables(self):
        maxIndex = self.logMax * self.stMax
        self.startAllMem = self.newVar((maxIndex), vtype=bool, name='startAllMem')
        self.startAllMemTimesBlockAllMemBin =  self.newVar((maxIndex), vtype=bool, name='startAllMemTimesBlockAllMemBin')                   
        self.endAllMem = self.newVar((maxIndex), vtype=bool, name='endAllMem')
        self.endAllMemTimesBlockAllMemBin =  self.newVar((maxIndex), vtype=bool, name='endAllMemTimesBlockAllMemBin')                   

        self.dictNumVariables['log*st'] += 4 # maximumStage
        pass


    def setupTouchesTableBeforeVariables(self):

        # firstRowOfTableBefore .. ordToLog(sl,log,ord) * firstRowOfOrd(sl, ord-1) for ord in 1 ..
        # numberOfRowsOfTablesBefore .. ordToLog(sl,log,ord) * numberOfRowsOfOrd(sl, ord-1) for ord in 1 ..
        # firstRowOfTableBeforeTimesNumberOfRowsOfTablesBeforeBinary

        self.touchesTableBefore = {}; self.firstRowOfTableBefore={}; self.numberOfRowsOfTableBefore={};
        self.numberOfRowsOfTableBeforeBinary={}; self.firstRowOfTableMinusLastRowOfTableBeforeBinary = {}
        self.firstRowOfTableMinusLastRowOfTableBeforeBinary = {};
        self.firstRowOfTableBeforeIfOrd = {}; self.numberOfRowsOfTableBeforeIfOrd = {};
        self.notFirstTableInAllSlicesBinary = {}
        for mem in self.switch.memoryTypes:
            maxIndex = sum(self.slMax[mem]) * self.logMax
            vname = 'firstRowOfTableBefore'
            ub = self.ub[mem]['firstRowOfOrd']
            self.ub[mem][vname] = ub
            self.firstRowOfTableBefore[mem] = self.newVar((maxIndex), vtype=int, lb=0, ub = ub, name=vname+mem)

            vname = 'numberOfRowsOfTableBefore'
            self.ub[mem][vname] = ub
            self.numberOfRowsOfTableBefore[mem] = self.newVar((maxIndex), vtype=int, lb=0, ub=ub, name=vname+mem)

            vname = 'numberOfRowsOfTableBeforeBinary'
            self.ub[mem][vname] = 1
            self.numberOfRowsOfTableBeforeBinary[mem] = self.newVar((maxIndex), vtype=int, lb=0, ub=1, name=vname+mem)

            vname = 'firstRowOfTableMinusLastRowOfTableBeforeBinary'
            self.ub[mem][vname] = 1
            self.firstRowOfTableMinusLastRowOfTableBeforeBinary[mem] =\
                self.newVar((maxIndex), vtype=int, lb=0, ub=1, name=vname+mem)


            vname = 'firstRowOfTableBeforeIfOrd' # ordToLog[log,ord,sl] * firstRowOfOrd[ord-1,sl]
            maxIndex = sum(self.slMax[mem]) * self.logMax * self.orderMax
            ub = self.ub[mem]['firstRowOfOrd']
            self.ub[mem][vname] = ub
            self.firstRowOfTableBeforeIfOrd[mem] = self.newVar((maxIndex), vtype=int, lb=0, ub = ub, name=vname+mem)

            vname = 'numberOfRowsOfTableBeforeIfOrd' # ordToLog[log,ord,sl] * numberOfRowsOfOrd[ord-1,sl]
            maxIndex = sum(self.slMax[mem]) * self.logMax * self.orderMax
            ub = self.ub[mem]['firstRowOfOrd']
            self.ub[mem][vname] = ub
            self.numberOfRowsOfTableBeforeIfOrd[mem] = self.newVar((maxIndex), vtype=int, lb=0, ub = ub, name=vname+mem)

            vname = 'notFirstTableInAllSlicesBinary'
            maxIndex = sum(self.slMax[mem]) * self.logMax
            self.notFirstTableInAllSlicesBinary[mem] = \
                self.newVar((maxIndex), vtype = int, lb=0, ub = 1, name= vname+mem)

            vname = 'touchesTableBefore'
            maxIndex =  sum(self.slMax[mem]) * self.logMax
            self.touchesTableBefore[mem] = self.newVar((maxIndex), vtype=int, lb=0, ub=1, name=vname+mem)
            pass
        pass



    def getXXOfLog(self, mem, log, sl, model=None):
        # 3 constraints
        """
        Change firstRow constraint to reflect the idea that 
        sum([numberOfRowsBinary[mem][log,sl1] * self.sliceOverlap(sl1,log,sl]) <= 1
        """
        # Logical table overlaps this slice in at most one assignment
        self.newConstr(sum([model[self.numberOfRowsBinary[mem]][self.iLSl(mem, log, sl1)] *\
                                  self.sliceOverlap(mem,sl1, log, sl)\
                                  for sl1 in self.slicesInSameStageAs(mem,sl) if sl1 <= sl]) <= 1)

        """
        second constraint: number of rows assigned total for this log in this
            slice is computed as numberOfRows
        """
        firstRow = sum([model[self.startRowTimesNumberOfRowsBinary[mem]][self.iLSl(mem,log,sl1)]\
                            * self.sliceOverlap(mem,sl1,log,sl)\
                            for sl1 in self.slicesInSameStageAs(mem, sl) if sl1 <= sl])

        self.newConstr(model[self.firstRowOfLog[mem]][self.iLSl(mem,log,sl)] == firstRow)


        numberOfRows = sum([model[self.numberOfRows[mem]][self.iLSl(mem,log,sl1)]\
                                * self.sliceOverlap(mem,sl1,log,sl)\
                                for sl1 in self.slicesInSameStageAs(mem, sl)  if sl1 <= sl])

        self.newConstr(model[self.numberOfRowsOfLog[mem]][self.iLSl(mem, log,sl)] == numberOfRows)
        self.testNumConstraints += 3
        pass

    def addProductConstraint(self, prod, cont, binary, ub):
        self.newConstr(prod <= ub * binary)
        self.newConstr(prod <= cont)
        self.newConstr(prod >= cont - ub * (1 - binary))
        self.newConstr(prod >= 0)
        pass

    def addProductBinaryConstraint(self, prod, binary1, binary2):
        self.newConstr(prod <= binary1)
        self.newConstr(prod <= binary2)
        self.newConstr(prod >= binary1 + binary2 - 1)
        pass

    def addBinaryConstraint(self, binary, cont, ub):
        self.newConstr(binary  <= cont)
        self.newConstr(binary * ub >= cont)
        pass

    def setupTouchesTableBeforeConstraints(self, model=None):
        self.tableBeforeConstraint(model)
        self.touchesTableBeforePerSliceConstraint(model)
        self.touchesAtleastOneTableBeforeConstraint(model)
        pass
    
    def tableBeforeConstraint(self,model=None):
        memXLogXSl = [(mem,log,sl)\
                          for mem in self.switch.memoryTypes\
                          for log in range(self.logMax)\
                          for sl in range(sum(self.slMax[mem]))]
        for mem,log,sl in memXLogXSl:
            totalFirstRow = 0
            totalNumberOfRows = 0

            for order in range(1,self.orderMax):
                prod = model[self.firstRowOfTableBeforeIfOrd[mem]][self.iSlOL(mem,sl,order,log)]
                cont = model[self.firstRowOfOrd[mem]][self.iOSl(mem,order-1,sl)]
                binary = model[self.ordToLog[mem]][self.iSlOL(mem,sl,order,log)]
                self.addProductConstraint(prod=prod,cont=cont,binary=binary,ub=self.ub[mem]['firstRowOfOrd'])
                totalFirstRow += prod   

                prod = model[self.numberOfRowsOfTableBeforeIfOrd[mem]][self.iSlOL(mem,sl,order,log)]
                cont = model[self.numberOfRowsOfOrd[mem]][self.iOSl(mem,order-1,sl)]
                binary = model[self.ordToLog[mem]][self.iSlOL(mem,sl,order,log)]
                self.addProductConstraint(prod=prod,cont=cont,binary=binary,ub=self.ub[mem]['numberOfRowsOfOrd'])
                totalNumberOfRows += prod
                pass
            
            self.newConstr(model[self.firstRowOfTableBefore[mem]][self.iLSl(mem,log,sl)] == totalFirstRow)
            self.newConstr(model[self.numberOfRowsOfTableBefore[mem]][self.iLSl(mem,log,sl)] == totalNumberOfRows)


            pass
        pass

    def touchesTableBeforePerSliceConstraint(self,model=None):
        memXLogXSl = [(mem,log,sl)\
                          for mem in self.switch.memoryTypes\
                          for log in range(self.logMax)\
                          for sl in range(sum(self.slMax[mem]))]
        for mem,log,sl in memXLogXSl:    
            ub = self.ub[mem]['numberOfRowsOfTableBefore']
            cont = model[self.numberOfRowsOfTableBefore[mem]][self.iLSl(mem,log,sl)]
            binary = model[self.numberOfRowsOfTableBeforeBinary[mem]][self.iLSl(mem,log,sl)]
            self.addBinaryConstraint(cont=cont,binary=binary,ub=ub)

            ub = self.ub[mem]['firstRowOfLog']
            cont = model[self.firstRowOfLog[mem]][self.iLSl(mem,log,sl)]\
                - model[self.numberOfRowsOfTableBefore[mem]][self.iLSl(mem,log,sl)]\
                - model[self.firstRowOfTableBefore[mem]][self.iLSl(mem,log,sl)]
            binary = model[self.firstRowOfTableMinusLastRowOfTableBeforeBinary[mem]][self.iLSl(mem,log,sl)]
            self.addBinaryConstraint(cont=cont,binary=binary,ub=ub)

            binary1 = model[self.numberOfRowsOfTableBeforeBinary[mem]][self.iLSl(mem,log,sl)]
            prod = model[self.touchesTableBefore[mem]][self.iLSl(mem,log,sl)]
            # is one when there is a table before it with some rows
            # and first row of this table = last row of that table + 1
            self.addProductBinaryConstraint(prod=prod,binary1=binary1,binary2=binary)
            pass
        pass

    def touchesAtleastOneTableBeforeConstraint(self, model=None):
        memXLogXSl = [(mem,log,sl)\
                          for mem in self.switch.memoryTypes\
                          for log in range(self.logMax)\
                          for sl in range(sum(self.slMax[mem]))]

        for (mem,log,sl) in memXLogXSl:
            hasRows = model[self.numberOfRowsBinary[mem]][self.iLSl(mem,log,sl)]
            touches = 0
            firstTableInSl = 0
            pf = self.preprocess.pfBlocks[mem][log]
            for sl2 in range(sl, sl+pf):
                touches += model[self.touchesTableBefore[mem]][self.iLSl(mem,log,sl)]
                # If number of rows is 0, ordToLog can be 1?
                firstTableInSl += model[self.ordToLog[mem]][self.iSlOL(mem,sl,0,log)]
                pass

            cont = pf - firstTableInSl # > 0 if not first table in all slices
            binary = model[self.notFirstTableInAllSlicesBinary[mem]][self.iLSl(mem,log,sl)]
            ub = pf + 1
            self.addBinaryConstraint(cont=cont,binary=binary,ub=ub)
            
            # If not first table in all slices and has rows, then touch >= 1
            # If first table in all slices and has rows, 0 + 1 - 1 .. 0
            # If not first table but has no rows .. 1 + 0 - 1 .. 0
            # If first table . no rows .. 0 + 0 -
            self.newConstr(touches >= binary + hasRows - 2)
            pass
    


    def getXXOfOrd(self, mem, order, sl, model=None):
        # 3 constraints
        # startRow and numberOfRows = 0, if no rows
        # at most one table per log in a slice
        numLogsPerOrder =\
            sum([model[self.ordToLog[mem]][self.iSlOL(mem, sl,order,log)]\
                     for log in range(self.logMax)])
        self.newConstr(numLogsPerOrder <= 1)

        
        self.newConstr(model[self.firstRowOfOrd[mem]][self.iOSl(mem,order,sl)] ==\
                             sum([model[self.firstRowOfLogTimesOrdToLog[mem]]\
                                      [self.iSlOL(mem, sl,order,log)]\
                                      for log in range(self.logMax)]))
            
        self.newConstr(model[self.numberOfRowsOfOrd[mem]][self.iOSl(mem,order,sl)] ==\
            sum([model[self.numberOfRowsOfLogTimesOrdToLog\
                     [mem]][self.iSlOL(mem, sl,order,log)]\
                     for log in range(self.logMax)]))
        self.testNumConstraints += 3

        pass


    def getStartingAndEndingStages(self, model=None):
        totalCon = 0
        for log in range(self.logMax):
            startStage = sum([model[self.startAllMem][self.iLSt(log,st)] * st for st in range(self.stMax)])
            anyBlocksInStartStage = sum([model[self.startAllMemTimesBlockAllMemBin][self.iLSt(log,st)] for st in range(self.stMax)])
            # there is exactly one starting stage
            self.newConstr(sum([model[self.startAllMem][self.iLSt(log,st)] for st in range(self.stMax)]) == 1)
            self.testNumConstraints += 1
            totalCon += 1
            # if a stage has blocks, starting stage is at least as small
            upperBound = self.stMax
            for st in range(self.stMax):
                self.newConstr(startStage <= st + (1 - model[self.blockAllMemBin][self.iLSt(log,st)]) * upperBound)
                self.testNumConstraints += 1
                totalCon += 1
                pass
            pass
            # starting stage has some blocks
            self.newConstr(anyBlocksInStartStage >= 1)
            self.testNumConstraints += 1
            totalCon += 1
            pass
        self.dictNumConstraints['log'] += 2
        self.dictNumConstraints['log*st'] += 1

        for log in range(self.logMax):
            endStage = sum([model[self.endAllMem][self.iLSt(log,st)] * st for st in range(self.stMax)])
            anyBlocksInEndStage = sum([model[self.endAllMemTimesBlockAllMemBin][self.iLSt(log,st)] for st in range(self.stMax)])
            # there is exactly one ending stage
            self.newConstr(sum([model[self.endAllMem][self.iLSt(log,st)] for st in range(self.stMax)]) == 1)                        
            self.testNumConstraints += 1
            totalCon += 1
            # if a stage has blocks, ending stage is at least as big
            upperBound = self.stMax
            for st in range(self.stMax):
                self.newConstr(endStage >= st - (1 - model[self.blockAllMemBin][self.iLSt(log,st)]) * upperBound)
                self.testNumConstraints += 1
                totalCon += 1
                pass
            pass
            # ending stage has some blocks
            self.newConstr(anyBlocksInEndStage >= 1)
            self.testNumConstraints += 1
            totalCon += 1
            pass
        self.dictNumConstraints['log'] += 2
        self.dictNumConstraints['log*st'] += 1

        logging.info('getStartingAndEndingStages')
        logging.info('added: %d' % totalCon)
        logging.info('computed: %d' % self.computeSum({
            'log':4,'log*st':2}))
        pass


    def overlapConstraint(self, mem, order, sl, model=None):
        # 2 constraints
        upperBound = (self.rowMax[mem]+1)*2
        nextOrd = self.iOSl(mem,order+1,sl)
        thisOrd = self.iOSl(mem,order,sl)
        
        # keep non empty tables together.. if order'th table has no rows
        # then order+1'th table has no rows too.
        # push all empty tables to the end (2 nonzero, 3 zero -> 5 order)
        self.newConstr(model[self.numberOfRowsOfOrdBinary[mem]][nextOrd] <= \
                         model[self.numberOfRowsOfOrdBinary[mem]][thisOrd])
        self.testNumConstraints += 1

        # next table (order+1) starts after order'th table starts
        # if order+1'th table has any rows
        eps = 0.01
        upperBound = eps + self.ub[mem]['firstRowOfOrd'] - self.lb[mem]['firstRowOfOrd']
        """
        self.newConstr(model[self.firstRowOfOrd[mem]][nextOrd] >=\
                             eps + model[self.firstRowOfOrd[mem]][thisOrd]\
                             - (2 - model[self.numberOfRowsOfOrdBinary[mem]][nextOrd]\
                                    - model[self.numberOfRowsOfOrdBinary[mem]][thisOrd]) * upperBound)
        """

        # next table (order+1) starts after order'th table ends
        # if order+1'th table has any rows (not needed?)
        upperBound = eps + self.ub[mem]['numberOfRowsOfOrd'] + self.ub[mem]['firstRowOfOrd']
        #    - 1 - self.lb[mem]['firstRowOfOrd']
        
        self.newConstr(model[self.firstRowOfOrd[mem]][nextOrd] >=\
                             eps + model[self.numberOfRowsOfOrd[mem]][thisOrd]\
                             + model[self.firstRowOfOrd[mem]][thisOrd] - 1\
                             - (2 - model[self.numberOfRowsOfOrdBinary[mem]][nextOrd]\
                                    - model[self.numberOfRowsOfOrdBinary[mem]][thisOrd]) * upperBound)
        self.testNumConstraints += 1
        

        pass
    
    def wordLayoutConstraint(self, model=None):
        for mem in self.switch.memoryTypes:
            for st in range(self.stMax):
                for log in range(self.logMax):
                    # Getting slices used by a logical table per stage
                    # in terms of numberOfRows
                    numSlices = \
                        sum([model[self.numberOfRowsOfLogBinary[mem]][self.iLSl(mem,log,sl)]\
                                 for sl in self.slicesInStage(mem,st)])
                    
                    self.newConstr(model[self.slices[mem]][self.iLSt(log,st)] == numSlices)
                    self.testNumConstraints += 1

                    # Getting words for a logical table per stage
                    # in terms of numberOfRows. FlexPipe allows
                    # one word per row.

                    numWords = \
                        sum([model[self.numberOfRows[mem]][self.iLSl(mem,log,sl)]\
                                 for sl in self.slicesInStage(mem,st)])
                    
                    self.newConstr(model[self.word[mem]][self.iLSt(log,st)] == numWords)
                    self.testNumConstraints += 1

                    pass
                pass
            pass
        self.dictNumConstraints['mem*log*st'] += 2
        pass

    
    def oneOrderPerLogConstraint(self, mem, sl, log, model=None):
        numOrdersPerLog =\
            sum([model[self.ordToLog[mem]][self.iSlOL(mem, sl,order,log)]\
                     for order in range(self.orderMax)])
        # if log overlaps this slice, then numOrdersPerLog is 1
        self.newConstr(numOrdersPerLog ==\
                             model[self.numberOfRowsOfLogBinary[mem]][self.iLSl(mem,log,sl)])
        self.testNumConstraints += 1
        pass

    def maximumTablesPerSliceConstraint(self, mem, sl, model=None):
        total = sum([model[self.numberOfRowsOfLogBinary[mem]][self.iLSl(mem,log,sl)]\
                         for log in range(self.logMax)])
        self.newConstr(total <= self.orderMax)
        self.testNumConstraints += 1
        pass

    def useMemoryConstraint(self, model=None):
        # assign blocks of logical table to tcam/ sram only if it's allowed
        for mem in self.switch.memoryTypes:
            upperBound = self.ub[mem]['slices']*self.stMax
            for log in range(self.logMax):
                totalSlices = sum([model[self.slices[mem]][self.iLSt(log, st)] for st in range(self.stMax)])
                logging.debug("preprocess.use["+mem+"]["+self.program.names[log]+"]")
                self.newConstr(totalSlices\
                                     <= self.preprocess.use[mem][log]*upperBound)
                self.testNumConstraints += 1
                pass
            pass
        self.dictNumConstraints['mem*log'] += 1
        pass
    
    
    def assignmentConstraint(self, model=None):
        for log in range(self.logMax):
            allocatedWords = sum([model[self.word[mem]][self.iLSt(log,st)]\
                                      for mem in self.switch.memoryTypes\
                                      for st in range(self.stMax)])
            self.newConstr((allocatedWords >= self.program.logicalTables[log]))
            self.testNumConstraints += 1
            pass
        self.dictNumConstraints['log'] += 1
        pass


    def dependencyConstraint(self, model=None):
        """
        If log2 match depends on log1, then last stage (TCAM/ SRAM)
        of log1 is strictly before first stage (TCAM/ SRAM) of log2.
        """
        eps = 0.1
        upperBound = self.stMax
        allStages = self.preprocess.toposortOrderStages
        for (log1,log2) in self.program.logicalSuccessorDependencyList:
            start2 = sum([model[self.startAllMem][self.iLSt(log2, st)] * st for st in allStages])
            end1 =  sum([model[self.endAllMem][self.iLSt(log1, st)] * st for st in allStages])
            self.newConstr(start2 >= end1)
            self.testNumConstraints += 1
            pass
        self.dictNumConstraints['succDep'] += 1

        for (log1,log2) in self.program.logicalMatchDependencyList:
            start2 = sum([model[self.startAllMem][self.iLSt(log2, st)] * st for st in allStages])
            end1 =  sum([model[self.endAllMem][self.iLSt(log1, st)] * st for st in allStages])
            self.newConstr(start2 >= eps + end1)
            self.testNumConstraints += 1
            pass
        self.dictNumConstraints['matchDep'] += 1

        # Flexpipe Action dependencies resolved at the end of a stage
        for (log1,log2) in self.program.logicalActionDependencyList:
            start2 = sum([model[self.startAllMem][self.iLSt(log2, st)] * st for st in allStages])
            end1 =  sum([model[self.endAllMem][self.iLSt(log1, st)] * st for st in allStages])
            self.newConstr(start2 >= end1)
            self.testNumConstraints += 1
            pass
        self.dictNumConstraints['actionDep'] += 1


        pass

    def capacityConstraintBySlice(self, mem, log, sl, model=None):
        index = self.iLSl(mem,log, sl)
        lastSlice = self.slicesInSameStageAs(mem,sl)[-1]
        if sl + self.preprocess.pfBlocks[mem][log] > lastSlice + 1:
            self.newConstr(model[self.numberOfRows[mem]][index] == 0)
            self.testNumConstraints += 1
        else:
            self.dictNumConstraints['constant'] -= 1
        pass

    def capacityConstraintByRow(self, mem, sl, model=None):
        upperBound = self.ub[mem]['firstRowOfOrd'] + self.ub[mem]['numberOfRowsOfOrd'] - self.rowMax[mem]
        for order in range(self.orderMax):
            index = self.iOSl(mem,order,sl)
            self.newConstr(model[self.firstRowOfOrd[mem]][index] + model[self.numberOfRowsOfOrd[mem]][index] <=\
                                 self.rowMax[mem] + (1 - model[self.numberOfRowsOfOrdBinary[mem]][index])\
                                 * upperBound)
            self.testNumConstraints += 1
            pass
        pass


    def setIlpResults(self):
        for mem in self.switch.memoryTypes:
            order = 0
            self.results['ilpUsedSlices'+mem] =\
                int(sum([round(self.m[self.numberOfRowsOfOrdBinary\
                                   [mem]][self.iOSl(mem, order, sl)])\
                                   for sl in range(sum(self.slMax[mem]))]))
            pass
            """
        for mem in self.switch.memoryTypes:
            # slice is used if first table has >0 rows
            order = 0
            usedSlices[mem] = sum([self.numberOfRowsOfOrdBinary\
                                       [mem][self.iOSl(mem, order, sl)]\
                                       for sl in range(sum(self.slMax[mem]))])
            pass
            """
        self.results['ilpTotalUsedSlices'] = sum([self.results['ilpUsedSlices'+mem]\
                                                  for mem in self.switch.memoryTypes])
        self.results['ilpTime'] = self.m.getSolverTime()
        self.results['ilpNumIterations'] = self.m.getNIterations()
        self.results['ilpSolved'] = True
        self.results['ilpNumRowsInModel'] = self.m.getNRows()
        self.results['ilpNumColsInModel'] = self.m.getNCols()
        self.results['ilpNumQCsInModel'] = self.m.getNQCs()
        self.results['ilpNumVariables'] = self.numVariables
        self.results['ilpNumConstraints'] = self.numConstraints

            
        pass


    def solve(self, program, switch, preprocess):
        self.setup(program, switch, preprocess)

        logging.info("Computing variables:")
        self.numVariables = self.computeSum(self.dictNumVariables)
        logging.info("alternatively counted constraints: %d" % self.testNumConstraints)
        logging.info("Computing Constraints:")
        self.numConstraints = self.computeSum(self.dictNumConstraints)

        logging.debug("Starting with Greedy Solution as input")
        model = self.variables
        obj = sum([model[self.totalSlicesBinary[mem]][st]\
                      for st in range(self.stMax)\
                      for mem in self.switch.memoryTypes])

        # self.getTotalUsedSlices(model=self.variables),\
        # obj = self.numberOfRowsOfOrd['ffu'][self.iOSl('ffu', 0, 8 )]
        # self.startingDict,\
        realVars = sorted([name for name in self.varType if self.varType[name] == 'real'])
        logging.info("%d real vars: %s" % (len(realVars), realVars))

        boolVars = sorted([name for name in self.varType if self.varType[name] == int and self.varUb[name] == 1])
        logging.info("%d bool vars: %s" % (len(boolVars), boolVars))

        #
        if self.mipstartFile == None:
            if len(self.startingDict) == 0:
               self.startingDict = None
            else:               
               mipStartFile = "%s_greedy_mipstart.mst"%self.outputFileName
               self.m.set_starting_dict(self.startingDict, mipStartFile)
            pass

        try:
            self.m.saveModel("%s_model.lp"%self.outputFileName)
        except Exception, e:
            logging.exception(e)
            pass


        try:
            self.m.minimize_populate(obj,\
                                starting_dict=None,\
                                relative_gap=self.relativeGap,\
                                epagap = self.epagap,\
                                emphasis=self.emphasis,\
                                populate_limit=self.populateLimit,\
                                solnpoolintensity=self.solnpoolintensity,\
                                tree_limit=self.treeLimit,\
                                time_limit=self.timeLimit,\
                                variable_select=self.variableSelect,\
                                work_mem=self.workMem,\
                                node_file_ind=self.nodeFileInd,\
                                work_dir=self.workDir,\
                                conflict_display = 2,\
                                write_level = self.writeLevel,
                                to_mipstart_file=None,
                                mipstart_file = self.mipstartFile)
            pass
        except Exception, e:
            print e
            logging.exception(e)
            pass

        if len(self.outputFileName) > 0:
            logging.info("Saving param basis, conflict files (e.g., %s_basis.bas)"%self.outputFileName)
            try:
                self.m.saveParam("%s_param.prm"%self.outputFileName)
            except Exception, e:
                logging.exception(e)
                pass
            try:
                self.m.saveBasis("%s_basis.bas"%self.outputFileName)
            except Exception, e:
                logging.exception(e)
                pass
            try:
                self.m.saveConflict("%s_conflict.lp"%self.outputFileName)
            except Exception, e:
                logging.exception(e)
                pass
            pass
        if not self.m.solved():
            return self.configs

        ####################################################
        logging.debug("Saving results from ILP")
        self.setIlpResults()

        ####################################################
        # Logging
        ####################################################        
        m = self.m
        config = FlexpipeConfiguration(program=program, switch=switch,\
                                   preprocess=preprocess, version="ILP")
        startRowDict = {}
        numberOfRowsDict = {}
        for mem in self.switch.memoryTypes:
            startRow = self.m[model[self.startRow[mem]]]
            numberOfRows = self.m[self.numberOfRows[mem]]
            shape = (self.logMax, sum(self.slMax[mem]))
            startRowDict[mem] = np.zeros(shape, dtype=np.int)
            numberOfRowsDict[mem] = np.zeros(shape, dtype=np.int)
            for log in range(self.logMax):
                for st in range(self.stMax):
                    for sl in self.slicesInStage(mem,st):
                        startRowDict[mem][log,sl] = startRow[self.iLSl(mem, log, sl)]
                        numberOfRowsDict[mem][log,sl] = numberOfRows[self.iLSl(mem, log,sl)]
                    pass
                pass
            pass
        config.configure(startRowDict, numberOfRowsDict)

        # JUST CHECKING IF ILP SOLUTION SATISFIES ITS OWN CONSTRAINTS
        ilpDict = {}
        self.fillModel(startRowDict, numberOfRowsDict, ilpDict)
        if self.touches:
            self.getTouchesStartingDictValues(model=ilpDict)
            pass
        logging.info("Checking ILP's solution")
        self.checkSolution(model=ilpDict)

        
        self.configs['ilpConfig'] = config
        #        logging.info(self.results)
        return self.configs

