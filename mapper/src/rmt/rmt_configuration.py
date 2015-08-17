import random
import numpy as np
import math
import textwrap

from datetime import datetime
import logging

from rmt_dependency_analysis import RmtDependencyAnalysis
from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph
from pygraph.algorithms.minmax import shortest_path
from pygraph.algorithms.critical import critical_path

import traceback

# PLOTTING MODULES
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
except:
    logging.info(traceback.print_exc())
    pass

class RmtConfiguration:
    def __init__(self, program, switch, preprocess,\
                     layout, version):
        self.logger = logging.getLogger(__name__)

        self.program = program
        self.da = RmtDependencyAnalysis(program)
        self.switch = switch
        self.preprocess = preprocess
        self.version = version
        self.stMax = self.switch.numStages
        self.logMax = self.program.MaximumLogicalTables

        self.typeColor = {'action': 'black'}
        for mem in self.switch.memoryTypes:
            self.typeColor[mem] = 'yellow'
            pass

        self.pfMax = {}
        for mem in self.switch.allTypes:
            self.pfMax[mem] = preprocess.layout[mem].shape[1]
            pass
        self.logger.debug("PFMAX: %s" % self.pfMax)
        self.configure(layout)
        pass

    def getWordsPerTable(self):
        packingUnits = {}
        wordsPerLog = {}

        for log in range(self.logMax):
            wordsPerLog[log] = {}
            for st in range(self.stMax):
                wordsPerLog[log][st] = 0
                pass
            pass
        
        for mem in self.switch.memoryTypes:
            packingUnits[mem] = {}
            for log in range(self.logMax):
                packingUnits[mem][log] = {}
                for st in range(self.stMax):
                    packingUnits[mem][log][st] = {}
                    packingUnitsPresent =\
                    [pf for pf in range(self.pfMax[mem])\
                    if self.layout[mem][log*self.stMax+st, pf] > 0]
                    if len(packingUnitsPresent) == 0:
                        continue
                    elif len(packingUnitsPresent) > 1:
                        roundOkay = \
                            (len([pf for pf in range(self.pfMax[mem])\
                                     if round(self.layout[mem]\
                                                  [log*self.stMax+st, pf]) > 0]) <= 1)
                        level = logging.WARNING
                        if not roundOkay:
                            self.logger.log(level, "For %s, More than 1 packing unit for %s (%s)" %\
                                                 (self.version, self.program.names[log], mem))
                            pass
                        pass
                    pf = packingUnitsPresent[0]
                    numPUnits = self.layout[mem][log*self.stMax+st, pf]
                    if len(self.preprocess.word[mem].shape) == 1:
                        wordsPerPUnit = self.preprocess.word[mem][log]
                        pass
                    else:
                        wordsPerPUnit = self.preprocess.word[mem][log][pf]
                        pass
                    wordsPerLog[log][st] += numPUnits * wordsPerPUnit
                    packingUnits[mem][log][st] =\
                      {'pf':pf, 'wordsPerPUnit':wordsPerPUnit,\
                       'numPUnits': numPUnits}
                    pass
                pass
            pass

        self.packingUnits = packingUnits
        self.wordsPerLog = wordsPerLog

        totalUnassignedWords = 0
        for log in range(self.logMax):
            wordsAssigned = np.floor(sum([wordsPerLog[log][st] for st in range(self.stMax)]))
            wordsNeeded = np.ceil(self.program.logicalTables[log])
            if wordsAssigned < wordsNeeded:
                totalUnassignedWords += wordsNeeded - wordsAssigned
                pass
            pass
        totalWordsNeeded = sum(self.program.logicalTables)
        self.totalUnassignedWords = int(round(totalUnassignedWords))
        self.logger.info("Total words unassigned %d out of %d (%.1f p.c.)" %\
                     (totalUnassignedWords, sum(self.program.logicalTables),\
                      float(totalUnassignedWords)/totalWordsNeeded))
        pass

    def checkWordsPerTable(self):
        totalUnassignedWords = 0
        for log in range(self.logMax):
            wordsAssigned = np.floor(sum([self.wordsPerLog[log][st] for st in range(self.stMax)]))
            wordsNeeded = np.ceil(self.program.logicalTables[log])
            satisfied = 100
            conj = 'and'
            if wordsAssigned < wordsNeeded:
                roundOkay =\
                    (sum([round(self.wordsPerLog[log][st]) for st in range(self.stMax)])\
                         >= wordsNeeded)
                level = logging.WARNING
                if not roundOkay:
                    level = logging.ERROR
                    pass
                totalUnassignedWords += wordsNeeded - wordsAssigned
                satisfied = float(wordsAssigned)/wordsNeeded
                conj = 'but'
                name = self.program.names[log]
                pU = ["%s in St %d" % (self.packingUnits[m][log][s],s)\
                      for m in self.switch.memoryTypes\
                      for s in range(self.stMax) if\
                      len(self.packingUnits[m][log][s])>0]

                self.logger.log(level, "For %s, %s needs %d %s assigned %d (%.1f p.c.):%s" %\
                             (self.version, name, wordsNeeded, conj, wordsAssigned, satisfied, pU))

                pass
            pass
        totalWordsNeeded = sum(self.program.logicalTables)
        self.logger.info("Total words unassigned %d out of %d (%.1f p.c.)" %\
                     (self.totalUnassignedWords, sum(self.program.logicalTables),\
                      float(self.totalUnassignedWords)/totalWordsNeeded))
        pass
    
    def configure(self, layout):
        self.layout = layout
        self.getWordsPerTable()
        blocks = {}
        totalBlocks = {}
        for st in range(self.stMax):
            blocks[st] = {}
            totalBlocks[st] = {}
            for log in range(self.logMax):
                blocks[st][log] = {}
                for thing in layout.keys():
                    blocks[st][log][thing] = 0
                    for pf in range(self.pfMax[thing]):
                        numPUnits = layout[thing][log*self.stMax+st, pf]
                        perPfBlocks = self.preprocess.layout[thing][log, pf]
                        if numPUnits > 0:
                            # bl = int(round(numPUnits)) * int(perPfBlocks)
                            bl = numPUnits * perPfBlocks
                            blocks[st][log][thing] += bl
                            pass
                        pass
                    pass
                # totalBlocks[st][log] = sum([round(blocks[st][log][t]) for t in blocks[st][log]])
                totalBlocks[st][log] = sum([blocks[st][log][t] for t in blocks[st][log]])
                pass
            pass
        self.blocks = blocks
        self.totalBlocks = totalBlocks
        pass

    def getNumActiveSrams(self):
        """
        For each table in each stage, 
        - number of RAMs for a match packing units (max if many types)
        - + number of RAMs for an action packing unit
        """

        ramsForPUnits = 0
        for st in range(self.stMax):
            for log in range(self.logMax):
                name = self.program.names[log]
                # match RAM
                ramsPerPUnit = []
                for pf in range(self.pfMax['sram']):
                    numPUnits = \
                        self.layout['sram'][log*self.stMax+st, pf]#)
                    numBlocks = self.preprocess.layout['sram'][log][pf]
                    if  numPUnits > 0:
                        ramsPerPUnit.append(numBlocks)
                        pass
                    pass
                if len(ramsPerPUnit) > 0:
                    if len(ramsPerPUnit) > 1:
                        self.logger.warn("For %s, %d PUnit types, %s match SRAM in %d" %\
                                         (self.version, len(ramsPerPUnit),name, st))
                        pass
                    ramsForPUnits += max(ramsPerPUnit)
                    pass
                # action RAM
                pf = 0
                ramsPerPUnit = self.preprocess.layout['action'][log][pf]
                numPUnits = self.layout['action'][log*self.stMax+st, pf]
                if numPUnits > 0:
                    ramsForPUnits += ramsPerPUnit
                    pass

                pass
            pass
        return ramsForPUnits

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
                    numPUnits =\
                        self.layout['tcam'][log*self.stMax+st, pf]
                        # round(self.layout['tcam'][log*self.stMax+st, pf])
                    tcamsForPUnits += numPUnits * (tcamWidth/matchWidth)
                    pass
                pass
            pass
        return tcamsForPUnits

    def getPowerForRamsAndTcams(self):
        numActiveSrams = self.getNumActiveSrams()
        numActiveTcams = self.getNumActiveTcams()                         
        powerForRamsAndTcams =\
            self.switch.power['wattsPerTcam'] * numActiveTcams +\
            self.switch.power['wattsPerSram'] * numActiveSrams
        self.logger.info("Need %.2fW for %.2f active RAMs and %.2f active TCAMs."%\
                         (powerForRamsAndTcams,numActiveSrams,numActiveTcams))

        return float(powerForRamsAndTcams)

    def getPipelineLatency(self):
        startTimes = self.getStartTimeOfStage()
        # if startTimes[0] < 0:
        #     return -1
        
        pipelineLatency = startTimes[self.stMax-1]
        # self.logger.info("Pipeline latency: ") + str(pipelineLatency)
        return pipelineLatency

    def getStartTimeOfStage(self):
        time = np.zeros(self.stMax)
        # assuming dependencies are satisfied
        endOf = [-1] * self.logMax
        startOf = [-1] * self.logMax

        satisified = True    
        for log in range(self.logMax):
            # why you need to round: self.blocks[.. is the exact decimal
            # value you get from the ILP solution, so it might be something
            # like 1e-70, which CPLEX would take as 0 in its calculations
            # for blockAllMemBin, startStage, pipelinLatency etc.
            # here too, we should round it to 0. Otherwise if a table
            # has 1e-70 blocks in stage st, we'd say st has blocks for
            # the table and starting stage is at least as small.
            # .. fixes the bug where ILP latency didn't match up with this.
            stages = [st for st in range(self.stMax)\
                          if round(sum([self.blocks[st][log][mem]\
                                      for mem in self.switch.memoryTypes])) > 0]
            if len(stages) == 0:
                satisfied = False
                break
            
            endOf[log] = max(stages)
            startOf[log] = min(stages)
            satisfied = not any([endOf[log]==-1, startOf[log]==-1])
            pass

        if not satisfied:
            self.logger.warn("For %s, some table didn't get assigned to any stage." % self.version)
            return [-1] * self.stMax

        succDeps = self.program.logicalSuccessorDependencyList
        warnStr = ""
        for (log1, log2) in succDeps:
            satisfied = startOf[log2] >= endOf[log1]
            if not satisified:
                warnStr += " %s ends in %d, %s starts in %d (s)" %\
                  (self.program.names[log1], endOf[log1],\
                   self.program.names[log2], startOf[log2])
                pass
            pass
        matchDeps = self.program.logicalMatchDependencyList
        for (log1, log2) in matchDeps:
            satisfied = startOf[log2] > endOf[log1]
            if not satisified:
                warnStr += " %s ends in %d, %s starts in %d (m)" %\
                  (self.program.names[log1], endOf[log1],\
                   self.program.names[log2], startOf[log2])
                pass
            pass
        actDeps = self.program.logicalActionDependencyList
        for (log1, log2) in actDeps:
            satisfied = startOf[log2] > endOf[log1]
            if not satisified:
                warnStr += " %s ends in %d, %s starts in %d (a)" %\
                  (self.program.names[log1], endOf[log1],\
                   self.program.names[log2], startOf[log2])
                pass

            pass

        if not satisfied:
            self.logger.warn("For %s: some dependency not satisifed, not checking latency: %s" %\
                                 (self.version, warnStr))
            return [-1] * self.stMax
        
        md = self.switch.matchDelay
        ad = self.switch.actionDelay
        sd = self.switch.successorDelay

        time[0] = 0
        for st in range(1,self.stMax):
            time[st] = max([time[st-1]+sd]+\
                [time[endOf[log1]] + md for (log1, log2) in matchDeps if startOf[log2] == st]+\
                [time[endOf[log1]] + ad for (log1, log2) in actDeps if startOf[log2] == st])
                #            self.logger.info("St " + str(st) + " starts at ") + str(time[st])
            pass
        return time
        pass
        

    def getColorsFromTableGroups(self, tableGroups):
        logColors = {}
        index = 1
        self.colorNames = {}
        f = open("colors.txt", "r")
        for line in f:
            words = line.split()
            if "white" in words[0].lower():
                continue
            self.colorNames[words[1]] = words[0]
            pass
        colors = sorted(self.colorNames.keys())
        random.seed(10)
        random.shuffle(colors)
        numColors = min(len(colors), len(tableGroups.keys()))
        groupColors = {}
        colorGroups = {}
        for code in self.colorNames.keys():
            colorGroups[self.colorNames[code]] = []
            pass
        for group in tableGroups.keys():
            groupName = "%s:%s" % (group, str(tableGroups[group]))
            colorIndex = (index + 1)%len(colors)
            color = colors[index%numColors]
            colorName = self.colorNames[color]
            groupColors[groupName] = colorName
            # group not groupName
            colorGroups[colorName].append(group)
            for table in tableGroups[group]:
                logColors[self.program.names.index(table)] = color
                pass
            index += 1
            pass

        for table in self.program.names:
            index = self.program.names.index(table)
            code = logColors[index]
            #print "%s: %s" % (table, code)
            pass
        """
        for d in [groupColors, colorGroups, logColors]:
            print "------"
            for k in sorted(d.keys()):
                if len(d[k]) > 0:
                    print "%s: %s" % (k, str(d[k]))
                    pass
                pass
            pass
        """
        return {'logColors': logColors, 'colorGroups': colorGroups, 'groupColors': groupColors}
        pass

    def showDict(self, d):
        string = ""
        for k in sorted(d.keys()):
            if len(d[k]) > 0:
                string += "%s: %s, " % (k, str(d[k]))
                pass
            pass
        return string

    def showList(sef, l):
        string = ""
        for index in range(len(l)):
            if len(l[index]) > 0:
                string += "%d: %s, " % (index, str(l[index]))
                pass
            pass
        return string
        
    def showPic(self, filename, prefix, tableGroups = {}, annotate=False):
        xLeft = 0
        yTop = 0
        xRight = 0
        yBottom = 0

        rect = {}
        if len(tableGroups) == 0:
            tableGroups = {}
            for name in self.program.names: 
                tableGroups[name] = [name]
                pass
            pass
        colors = self.getColorsFromTableGroups(tableGroups)
        logColors = colors['logColors']
        subplots = {}
        memoryTypes = sorted(self.switch.memoryTypes, reverse=True)
        numSubplots = len(memoryTypes)
        fig = plt.figure(1)
        for i in range(numSubplots):
            subplots[memoryTypes[i]] = fig.add_subplot(numSubplots,1,i)
            pass


        tablesPerStage = {}
        
        self.logger.debug(self.switch.memoryTypes)
        for mem in self.switch.memoryTypes:
            tablesPerStage[mem] = []
            self.logger.debug("In memory: " + mem)

            ax = subplots[mem]
            rect[mem] = [[] for log in range(self.program.MaximumLogicalTables)]
            maxY = self.switch.depth[mem] * self.switch.numSlices[mem][0]
            minY = 0
            minX = 0
            maxX = self.switch.width[mem] * self.switch.numStages
            ax.set_xlim([minX,maxX])
            ax.set_ylim([minY,maxY])
            
            for st in range(self.switch.numStages):
                tablesPerStage[mem].append([])
                xLeft = st * self.switch.width[mem]
                ax.add_line(matplotlib.lines.Line2D([xLeft,xLeft],[minY,maxY], lw=1, color='k'))
                startBlock = 0
                for log in range(self.program.MaximumLogicalTables):
                    totalMemBlocks = 0
                    for thing in self.switch.typesIn[mem]:
                        numThingBlocks = self.blocks[st][log][thing]
                        color = self.typeColor[thing]
                        totalMemBlocks += numThingBlocks
                        if thing in self.switch.memoryTypes:
                            color = logColors[log]
                            pass
                        
                        if numThingBlocks > 0:
                            yTop = maxY - startBlock * self.switch.depth[mem] # e.g., Row 0 at y=1000
                            height = numThingBlocks * self.switch.depth[mem]
                            yBottom = yTop - height
                            width = self.switch.width[mem]
                            patch = matplotlib.patches.Rectangle((xLeft, yBottom),\
                                                                     width,height,\
                                                                     color=color)
                            ax.add_patch(patch)
                            pass
                        startBlock += numThingBlocks
                        pass

                    if totalMemBlocks > 0:
                        text = self.program.names[log]
                        if totalMemBlocks >= 6:
                            text += " (%s)" % self.colorNames[logColors[log]]
                            pass
                        tablesPerStage[mem][st].append(text)
                        pass
                    pass
                startOfStage = xLeft
                ax.annotate(str(st), (startOfStage, minY) , color='r')
                ax.add_line(matplotlib.lines.Line2D([startOfStage, startOfStage],[minY,maxY], lw=5, color='k'))
                pass                
            self.logger.debug("Done with " + mem)
            pass

        i = 2
        for mem in self.switch.memoryTypes:
            figText = plt.figure(i)
            i += 1
            ax = figText.add_subplot(111)
            tablesPerStagePara = textwrap.fill("%s: " % mem.upper() +\
                                                   self.showList(tablesPerStage[mem]))
            ax.text(0, 0.5, tablesPerStagePara, fontsize=10)
            pass

        figText = plt.figure(i)
        ax = figText.add_subplot(111)
        colorGroupsPara = textwrap.fill("LEGEND: " + self.showDict(colors['colorGroups']))

        ax.text(0, 0.5, colorGroupsPara, fontsize=10)
        numFigs = i
        
        t = datetime.now()
        picFile = prefix + filename + ".pdf"
        pp = PdfPages(picFile)
        for i in range(1,numFigs+1):
            pp.savefig(i)
            pass
        pp.close()
        plt.close('all')
        pass

    def getEarliestStageFromAssign(self, assignInfo):
        gr = self.da.getDigraph()
        earliestStageFromAssign = {}
        for table in self.program.names:
            previousTables = gr.neighbors(table)
            previousTablesAssigned = True
            for prev in previousTables:
                if prev == 'start':
                    continue
                if prev not in assignInfo\
                        or 'end' not in assignInfo[prev]\
                        or assignInfo[prev]['end'] == -1:
                    self.logger.warn("For %s, %s must be assigned before assigning %s"\
                                     % (self.version, prev, table))
                    previousTablesAssigned = False
                    pass
                pass
            earliestStages = []
            if previousTablesAssigned:
                for prev in previousTables:
                    if prev == 'start':
                        continue
                    prevEnd = assignInfo[prev]['end']
                    edge = (table,prev)
                    edgeWeight = int(abs(gr.edge_weight(edge)))
                    tableStart = prevEnd + edgeWeight
                    attr = gr.edge_attributes(edge)
                    props = {"type":""}
                    for key, val in attr:
                        props[key] = val
                        pass
                    edgeType = props["type"]
                    earliestStages.append((tableStart, edgeType, prev, prevEnd))
                    pass
            earliestStageFromAssign[table] =\
                sorted(earliestStages, key = lambda tup: tup[0], reverse=True)
            pass
        return earliestStageFromAssign

    def display(self, paths = []):

        self.logger.info("Words per table")
        self.checkWordsPerTable()
        
        self.logger.info("Fraction of TCAMs/ SRAMs used")
        self.displayFractionUsed()
        
        self.logger.info("\n(%s) Power for RAMs and TCAMs " % self.version + str(self.getPowerForRamsAndTcams()))
        self.logger.info("\n(%s) Pipeline Latency " % self.version + str(self.getPipelineLatency()))

        self.logger.info("\n(%s)Start Time of Stages " % self.version) 
        startTime = self.getStartTimeOfStage()
        for st in range(self.stMax):
            self.logger.info("St " + str(st) + ": " + str(startTime[st]))
            pass
        
        
        summaryInfo = ""
        layoutInfo = ""

        
        layoutPerSt = {}
        summaryPerSt = {}
        stageInfo = {}
        perLogProgramInfo = self.da.getPerLogProgramInfo()
        for st in range(self.stMax):
            layoutPerSt[st] = {}
            summaryPerSt[st] = []
            stageInfo[st] = ""
            for log in range(self.logMax):
                if self.totalBlocks[st][log] > 0:
                    name = self.program.names[log]
                    summaryPerSt[st].append("%s (%d)" % (name, perLogProgramInfo[name]['earliestStage']))
                    layout = ", ".join(["%d %s" % (self.blocks[st][log][t],t[0])\
                                            for t in self.blocks[st][log]\
                                            if self.blocks[st][log][t] > 0])
                    layoutPerSt[st][log] = "%s (%s)  " % (name, layout)
                    pass
                pass
            
            totalMatchBlocks = {}
            for mem in self.switch.memoryTypes:
                totalMatchBlocks[mem] = sum([self.blocks[st][log][thing]\
                                                 for log in range(self.logMax) for\
                                                 thing in self.switch.typesIn[mem]])
                pass

            text = ", ".join(["%d %ss" % (totalMatchBlocks[mem], mem.upper()) for mem in self.switch.memoryTypes])
            stageInfo[st] = "Stage %d (%s): " % (st, text)
                
            pass
        
        self.logger.info("\n(%s) Tables allocated per stage\n" % self.version + summaryInfo)
        for st in sorted(summaryPerSt.keys()):
            if len(summaryPerSt[st]) > 0:
                self.logger.info("%s: %s" % (stageInfo[st], ",".join(summaryPerSt[st])))
                pass
            pass
        
        self.logger.info("\n(%s) Blocks allocated per stage\n" % self.version + layoutInfo)
        for st in sorted(layoutPerSt.keys()):
            if len(layoutPerSt[st]) > 0:
                sortedLogs = sorted(layoutPerSt[st].keys(),\
                                        key = lambda log: self.totalBlocks[st][log], reverse = True)
                layouts = ", ".join([layoutPerSt[st][log] for log in sortedLogs])
                self.logger.info("%s: %s" % (stageInfo[st], layouts))
                pass
            pass

        assignInfo =  self.getPerLogAssignInfo()

        self.logger.info("\n(%s) Table xx can't start before [(st, dependency, prev, prevEndSt),..]" % self.version)
        notBefore = self.getEarliestStageFromAssign(assignInfo)
        for table in self.program.names:
            previousTables = notBefore[table]
            self.logger.info("%s  : %s" % (table, previousTables))
            pass

        """
        For each table, if it's not in the earliest stage, show
        longest path to table, with dependency type, for what fields
        which stages each table is in
        For each stage, each resource usage
        """

        pass

    def getPerLogAssignInfo(self):
        # total blocks from stage .. through ..
        blocks = self.blocks
        perLogAssignInfo = {}
        for log in range(self.logMax):
            totalMemBlocks = {}
            for mem in self.switch.memoryTypes:
                totalMemBlocks[mem] = sum([blocks[st][log][mem]\
                                       for st in range(self.stMax)\
                                               for thing in self.switch.typesIn[mem]])
                pass
            
            inStages = [st for st in range(self.stMax)\
                                  if any([blocks[st][log][mem] > 0\
                                              for mem in blocks[st][log].keys()])]
            if len(inStages) > 0:
                startStage = min(inStages)
                endStage = max(inStages)
                pass
            else:
                startStage = -1
                endStage = -1
                pass

            name = self.program.names[log]
            perLogAssignInfo[name] = {'start': startStage, 'end': endStage}
            for mem in self.switch.memoryTypes:
                perLogAssignInfo[name][mem] = totalMemBlocks[mem]
                pass
            perLogAssignInfo[name]['blocksInfo'] = ", ".join("%d %s" % (perLogAssignInfo[name][t], t[0])\
                                                             for t in self.switch.memoryTypes\
                                                             if perLogAssignInfo[name][t] > 0)
            perLogAssignInfo[name]['stageInfo'] = " in st %d" % startStage
            if not startStage == endStage:
                perLogAssignInfo[name]['stageInfo'] = " in st %d" % perLogAssignInfo[name]['start']
                pass
            pass
        return perLogAssignInfo


    def displayFractionUsed(self):
        stagesUsed = [st for st in range(self.stMax) if\
                                 sum([self.blocks[st][log][mem]
                                      for mem in self.switch.memoryTypes\
                                      for log in range(self.logMax)]) >= 1]
        numStagesUsed = 0
        if len(stagesUsed) > 0:
            numStagesUsed = max(stagesUsed)
                                        
        self.logger.info("(%s) Number of stages used -%d" % (self.version, numStagesUsed+1))

        self.logger.info("Total in all # stages -")
        self.logger.info(self.blocks[st][log].keys())

        for mem in self.switch.memoryTypes:
            usedBlocks = sum([self.blocks[st][log][thing]\
                                  for log in range(self.logMax)\
                                  for st in range(self.stMax)\
                                  for thing in self.switch.typesIn[mem]])

            totalBlocks = sum(self.switch.numSlices[mem])
            self.logger.info("(%s) %d Total %ss used (%.1f pc)" %\
                             (self.version, usedBlocks, mem.upper(),\
                                  round((100.0 * usedBlocks)/totalBlocks)))

            pass

        for st in range(numStagesUsed):
            self.logger.info("Ingress Stage%d -" % st)
            for mem in self.switch.memoryTypes:
                usedBlocks = sum([self.blocks[st][log][thing]\
                                      for log in range(self.logMax)\
                                      for thing in self.switch.typesIn[mem]])

                totalBlocks = self.switch.numSlices[mem][st]
                numTables = sum([1 for log in range(self.logMax)\
                                          if self.blocks[st][log][mem] > 0])

                if (usedBlocks > totalBlocks):
                    roundOkay = (sum([round(self.blocks[st][log][thing])\
                                         for log in range(self.logMax)\
                                         for thing in self.switch.typesIn[mem]]) <= totalBlocks)
                    level = logging.WARNING
                    if not roundOkay:
                        level = logging.ERROR
                        pass
                    self.logger.log(level, "For %s: More blocks used (%d) than available (%d) in St %d" %\
                                 (self.version, usedBlocks, totalBlocks, st))
                    pass
                self.logger.info("(%s) %d Total %ss used (%.1f pc), %d Tables" %\
                                 (self.version, usedBlocks, mem.upper(),\
                                      round((100.0 * usedBlocks)/totalBlocks),\
                                                numTables))
                pass
            pass
        pass
    
    def displayInitialConditions(self):
        self.logger.info("(%s) Initial conditions" % self.version)

        self.logger.info("number of entries in logical table")
        self.showIntList(self.program.logicalTables, self.program.names, extra_arrs=[self.program.logicalTableWidths, self.preprocess.use['tcam'].T], arr_names=["#entries", "width", "TCAM use"])
        self.logger.info("action data widths for each logical table")
        for log in range(self.logMax):
            self.logger.info(self.program.names[log] + ": " \
                + str(self.program.logicalTableActionWidths[log]))
            pass
        pass
        
    def showIntList(self, arr, names=[], extra_arrs=[], arr_names=[]):
        arrs = [arr]
        string = ""
        if len(extra_arrs) > 0:
            for extra_arr in extra_arrs:
                arrs.append(extra_arr)

        string += ("".ljust(10)+ "\t")
        for i in range(len(arr_names)):
            string += (arr_names[i] + "\t")
        string += ("\n")

        rows = len(arr)
        for i in range(rows):
            if (len(names) > 0):
                string += (names[i].ljust(10) + "\t")
		for arr in arrs:
                    if int(round(arr[i]))/1000 >= 1:
                        string += (str(int(round(arr[i]))/1000) + "k\t")
                    else:
                        string += (str(int(round(arr[i]))) + "\t")
                    pass
                pass
            pass
            string += "\n"
        self.logger.info("(%s)\n" % self.version + string)
        pass

    def showInt(self, num):
        if int(round(num))/1000 >= 1:
            return(str(int(round(num))/1000) + "k")
        else:
            return(str(int(round(num))))

    def showIntArray(self, arr, names=[]):
        string = ""
        rows, cols = arr.shape
        for i in range(rows):
            if (len(names) > 0):
                string += (names[i].ljust(10) + "\t")
                pass
            for l in range(cols):
                if int(round(arr[i,l]))/1000 >= 1:
                    string += (str(int(round(arr[i,l]))/1000) + "k\t")
                elif arr[i,l] > 0.01:
                    string += (str(int(round(arr[i,l]))) + "\t")
                pass
            string += "\n"
            pass
        self.logger.info("(%s) " % self.version + string)
        pass
    
    def makeArrayToList(self, arr):
        """
        Makes an encapsulated array [[2], [5], [4]] into a list [2, 5, 4].
        """
        ret = np.array([])
        rows, cols = arr.shape
        for i in range(rows):
            for l in range(cols):
                ret = np.append(ret, arr[i,l])
                pass
            pass
        pass
        return ret.tolist()
