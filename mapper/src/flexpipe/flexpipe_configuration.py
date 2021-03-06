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
import math
from datetime import datetime
import logging
from flexpipe_dependency_analysis import FlexpipeDependencyAnalysis
import random
import textwrap

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


class FlexpipeConfiguration:
    """
    Module to describe and log a FlexPipe switch configuration
    for a given program
    """
    def __init__(self, program, switch, preprocess, version):
        self.logger = logging.getLogger(__name__)

        self.program = program
        self.switch = switch
        self.preprocess = preprocess
        self.version = version
        self.da = FlexpipeDependencyAnalysis(program)
        self.stMax = self.switch.numStages
        self.logMax = self.program.MaximumLogicalTables

        pass

    def displayInitialConditions(self):
        pass

    def getPerLogAssignInfo(self):
        """
         Return mapping from table to assignment info
          'start': start stage (or -1 if not valid)
          'end': end stage (or -1 if not valid)
        """
        rows = self.numberOfRows
        perLogAssignInfo = {}
        for log in range(self.logMax):            
            inStages = [st for st in range(self.stMax)\
                                  if any([rows[mem][log,sl] > 0\
                                              for mem in rows.keys()\
                                              for sl in self.preprocess.blocksInStage(mem,st)])
                                             ]
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
        return perLogAssignInfo


    def getEarliestStageFromAssign(self, assignInfo):
        """ Returns a mapping from tables
        to information about the first stage they could have started
        in- a table must start after all the tables it depends on
        have been completely assigned. The informations is a list of
         lists [@st, @dep, @prev, @prevEnd] which should be read as        
        Table xx can't start before stage @st because of @dependency
        on table @prev which ends in stage @prevEnd, one for each
        @prev that the table depends on.
        """
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

    def configure(self, startRow, numberOfRows):
        self.startRow = startRow
        self.numberOfRows = numberOfRows
        pass
    
    def display(self):
        """ Display configuration- tables in each memory type,
        in each stage.
        """
        
        tableGroups = {}
        for name in self.program.names: 
            tableGroups[name] = [name]
            pass
        colors = self.getColorsFromTableGroups(tableGroups)
        logColors = colors['logColors']

        self.logger.info("\n(%s) Rows allocated per stage\n" % self.version)
        memoryTypes = self.switch.memoryTypes
        for mem in memoryTypes:
            self.logger.info("(%s) In memory: %s" % (self.version, mem))
            for st in range(self.switch.numStages):
                self.logger.info("(%s) In stage %d" % (self.version, st))
                for sl in self.preprocess.blocksInStage(mem, st):
                    for log in range(self.program.MaximumLogicalTables):
                        numRows = self.numberOfRows[mem][log,sl]
                        if numRows > 0:
                            startRow = self.startRow[mem][log,sl]
                            numSl = int(self.preprocess.pfBlocks[mem][log])
                            self.logger.info(\
                                "(%s) " % self.version +\
                                "Table %s " % self.program.names[log] +\
                                    "start sl %d, row %d; " % (sl, startRow) +\
                                    "%d blocks wide, %d rows deep; color %s"\
                                    % (numSl, numRows, logColors[log]))
                            pass # if numRows > 0
                        pass # for log
                    pass # for sl
                pass # for st
            pass # for mem

        assignInfo =  self.getPerLogAssignInfo()

        self.logger.info("\n(%s) Table xx can't start before stage @st because of @dependency on table @prev which ends in stage @prevEndSt [(st, dependency, prev, prevEndSt),..]" % self.version)
        notBefore = self.getEarliestStageFromAssign(assignInfo)
        for table in self.program.names:
            previousTables = notBefore[table]
            self.logger.info("%s  : %s" % (table, previousTables))
            pass

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
            #print("%s: %s" % (table, code))
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

    def showPic(self, prefix, filename, tableGroups = {}, annotate=False):
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

        tablesPerStage = {}
        fig = {}
        memoryTypes = self.switch.memoryTypes
        figNum = 1
        for mem in memoryTypes:
            tablesPerStage[mem] = []
            fig[mem] = plt.figure(figNum)
            figNum += 1
            self.logger.info("(%s) In memory: %s" % (self.version, mem))
            ax = fig[mem].add_subplot(111)
            rect[mem] = [[] for log in range(self.program.MaximumLogicalTables)]
            maxY = self.switch.depth[mem]
            minY = 0
            minX = 0
            maxX = sum([len(self.preprocess.blocksInStage(mem, st))\
                           for st in range(self.switch.numStages)])\
                           * self.switch.width[mem]
            
            ax.set_xlim([minX,maxX])
            ax.set_ylim([minY,maxY])
            
            for st in range(self.switch.numStages):
                tablesPerStage[mem].append({})
                
                for sl in self.preprocess.blocksInStage(mem, st):
                    xLeft = sl * self.switch.width[mem]
                    ax.add_line(matplotlib.lines.Line2D([xLeft,xLeft],[minY,maxY], lw=1, color='k'))
                    for log in range(self.program.MaximumLogicalTables):
                        numRows = self.numberOfRows[mem][log,sl]
                        startRow = self.startRow[mem][log,sl]
                        
                        if numRows > 0:
                            yTop = maxY - startRow # e.g., Row 0 at y=1000
                            height = numRows
                            yBottom = yTop - numRows
                            width = int(self.preprocess.pfBlocks[mem][log]) * self.switch.width[mem]
                            patch = matplotlib.patches.Rectangle((xLeft, yBottom),\
                                                                     width,height,\
                                                                     color=logColors[log])
                            self.logger.info("(%s) %s in mem %s, stage %d, block %d in rows %d .. %d (%s)" %\
                                         (self.version, self.program.names[log], mem, st, sl,
                                          startRow, startRow+numRows, logColors[log]))
                            ax.add_patch(patch)
                            if (annotate):
                                ax.annotate(self.program.names[log],\
                                                (xLeft+width/2,\
                                                     yTop-height/2),\
                                                color='b', ha='center',\
                                                va='center')
                                pass
                            tableName = self.program.names[log]
                            if not tableName in tablesPerStage[mem][st]:
                                tablesPerStage[mem][st][tableName] =\
                                  {'index':len(tablesPerStage[mem][st]), 'numRows': numRows}
                                pass
                            else:
                                tablesPerStage[mem][st][tableName]['numRows'] += numRows
                                pass
                                
                            pass
                        pass
                    pass
                startOfStage = xLeft
                ax.annotate(str(st), (startOfStage, minY) , color='r')
                ax.add_line(matplotlib.lines.Line2D([startOfStage, startOfStage],[minY,maxY], lw=5, color='k'))
                pass
            ax.annotate("%s %s" % (mem, [st for st in range(self.switch.numStages)\
                                             if self.switch.numBlocks[mem][st]>0]),\
                            (5,5), color='g')

            t = datetime.now()
            pass

        i = len(self.switch.memoryTypes)+1
        for mem in self.switch.memoryTypes:
            text = "%s: " % mem
            figText = plt.figure(i)
            i += 1
            ax = figText.add_subplot(111)

            for st in range(self.switch.numStages):
                tablesPerStageText = {}
                for t in tablesPerStage[mem][st]:
                    val = tablesPerStage[mem][st][t]
                    index = val['index']
                    numRows = val['numRows']
                    tableIndex = self.program.names.index(t)
                    tablesPerStageText[index] = t
                    if numRows > 5:
                        tablesPerStageText[index] = "%s (%s/%s)" % (t,\
                                                                    self.colorNames[logColors[tableIndex]],\
                                                                    logColors[tableIndex])
                        pass
                    pass
                if len(tablesPerStageText) > 0:
                    text += ", St %d: " % st
                    text += ", ".join(tablesPerStageText[index] for index in sorted(tablesPerStageText.keys()))
                    pass
                pass
            
            tablesPerStagePara = textwrap.fill(text)
            ax.text(0, 0.5, tablesPerStagePara, fontsize=10)
            pass

        numFigs = i

        picFile = prefix + filename + ".pdf"
        pp = PdfPages(picFile)
        for i in range(1, numFigs):
            pp.savefig(i)
            pass
        pp.close()
        plt.close('all')
        pass

