import numpy as np
import math
import matplotlib
import textwrap
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
import logging

from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph
from pygraph.algorithms.minmax import shortest_path
from pygraph.algorithms.minmax import shortest_path_bellman_ford
from pygraph.algorithms.critical import critical_path

class FlexpipeDependencyAnalysis:
    def __init__(self, program):
        self.program = program
        self.logMax = self.program.MaximumLogicalTables
        pass

    # THINGS YOU CAN DO WITH JUST THE PROGRAM
    def getDigraph(self):
        program = self.program
        gr = digraph()
        gr.add_nodes(program.names)
        gr.add_nodes(['start','end'])
                     
        for pair in program.logicalSuccessorDependencyList:
            log1 = program.names[pair[0]]
            log2 = program.names[pair[1]]
            logging.debug("adding successor edge " + log1 + " -> " + log2)
            gr.add_edge((log2,log1),0, attrs=[("type", "SUCCESSOR")])
            pass

        for pair in program.logicalMatchDependencyList:
            log1 = program.names[pair[0]]
            log2 = program.names[pair[1]]
            logging.debug("adding match edge " + log1 + " -> " + log2)
            gr.add_edge((log2,log1),-1, attrs=[("type", "MATCH")])
            pass

        for pair in program.logicalActionDependencyList:
            log1 = program.names[pair[0]]
            log2 = program.names[pair[1]]
            logging.debug("adding action edge " + log1 + " -> " + log2)
            gr.add_edge((log2,log1),-1, attrs=[("type", "ACTION")])
            pass

        for log in program.names:
            if gr.neighbors(log) == []:
                gr.add_edge((log, 'start'),0, attrs=[("type", "SUCCESSOR")])
                logging.debug("adding edge " + " start " + " -> " + log)
                pass
            if gr.incidents(log) == []:
                gr.add_edge(('end',log),0, attrs=[("type", "SUCCESSOR")])
                logging.debug("adding edge " + log + " -> " + " end ")
                pass
            pass
        return gr
    
    def getDigraphFromStartNegative(self):
        originalGr = self.getDigraph()
        gr = digraph()
        for node in originalGr.nodes():
            gr.add_node(node)
            pass

        for edge in originalGr.edges():
            newEdge = (edge[1], edge[0])
            gr.add_edge(newEdge, wt=originalGr.edge_weight(edge),\
                            attrs=originalGr.edge_attributes(edge))

            pass

        return gr

    def makePath(self, nodes, gr):
        path = []
        totalEdgeWeight = 0
        for index in range(len(nodes)-1):
            node1 = nodes[index]
            node2 = nodes[index+1]
            edge = (node1, node2)
            edgeWeight = abs(gr.edge_weight(edge))
            attrs = gr.edge_attributes(edge)
            props = {"type":""}
            for (key, val) in attrs:
                props[key] = val
                pass

            totalEdgeWeight += edgeWeight
            path.append({'node1':node1,\
                             'node2':node2,\
                             'edgeWeight':edgeWeight,\
                             'totalEdgeWeight':totalEdgeWeight,\
                             'type': props["type"],\
                             'index': index})
            pass
        return path

    def showPath(self, path, nodeInfo=None):
        if len(path) == 0:
            logging.warn("EMPTY PATH")
            return ""

        pathStr = path[0]['node1']
        sym = {"MATCH": "=>", "ACTION": "~>", "SUCCESSOR": "->", "DEFAULT": "->"}
        for tup in path:
            if len(tup['type']) > 0 and tup['type'] in sym:
                pathStr += " %s " % sym[tup['type']]
                pass
            else:
                pathStr += " -> "
                pass
            pathStr += "%s (%d)" % (tup['node2'], tup['totalEdgeWeight'])
            if not nodeInfo == None and tup['node2'] in nodeInfo and 'stageInfo' in nodeInfo[tup['node2']]:
                pathStr += "%s " % nodeInfo[tup['node2']]['stageInfo']
                pass
            pathStr
            pass
        return pathStr

    def getPerLogProgramInfo(self):
        perLogProgramInfo = {}

        grFromStart = self.getDigraphFromStartNegative()

        #        grFromEnd = self.getDigraph()
        spanningTreeFromStart, maxDistFromStart = shortest_path_bellman_ford(grFromStart, 'start')
        tables = spanningTreeFromStart.keys()

        def getLongestPath(table):
            index = 0
            nextTable = table
            nodes = []
            pathStr = "Longest path from start to %s: " % table
            while index < len(spanningTreeFromStart):
                nodes.append(nextTable)
                nextTable = spanningTreeFromStart[nextTable]
                if nextTable in [None]:
                    break
                index += 1
                pass
            nodes = [n for n in reversed(nodes)]
            path = self.makePath(nodes, grFromStart)            
            pathStr += self.showPath(path)
            #logging.info(pathStr)
            return path

        grFromEnd = self.getDigraph()
        spanningTreeFromEnd, maxDistFromEnd = shortest_path_bellman_ford(grFromEnd, 'end')

        for t in tables:
            perLogProgramInfo[t] =\
                {'earliestStage': abs(maxDistFromStart[t]),\
                     'distanceFromEnd': abs(maxDistFromEnd[t]),\
                     'longestPathFromStart': getLongestPath(t)}
            pass
        return perLogProgramInfo

    def getDigraphFromEndPositive(self):
        originalGr = self.getDigraph()
        gr = digraph()
        for node in originalGr.nodes():
            gr.add_node(node)
            pass
        for edge in originalGr.edges():
            gr.add_edge(edge, wt=-originalGr.edge_weight(edge),\
                            attrs=originalGr.edge_attributes(edge))
            pass
        return gr

    def getDigraphFromStartPositive(self):
        originalGr = self.getDigraphFromStartNegative()
        gr = digraph()
        for node in originalGr.nodes():
            gr.add_node(node)
            pass
        for edge in originalGr.edges():
            gr.add_edge(edge, wt=abs(originalGr.edge_weight(edge)),
                        attrs=originalGr.edge_attributes(edge))
            pass
        return gr

    def showCriticalPath(self):
        gr = self.getDigraphFromStartPositive()
        criticalPath = critical_path(gr)
        nodes = [n for n in criticalPath]
        logging.info("nodes %s" % str(nodes))
        path = self.makePath(nodes, gr)
        pathStr = self.showPath(path)
        numMADeps =  path[-1]['totalEdgeWeight']
        logging.info("critical path: %s, %d match/action deps- " % (pathStr, numMADeps)+\
                         "needs %d stages" % (numMADeps + 1))
        return path
    pass
    
