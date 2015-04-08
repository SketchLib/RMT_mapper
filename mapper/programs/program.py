import numpy as np
import logging

class Program:
    def logicalDependencyMatrix(self, logicalDependencyList):
        D = np.zeros((self.MaximumLogicalTables, self.MaximumLogicalTables))
        for pair in logicalDependencyList:
            D[pair[0], pair[1]] = 1
            pass
        return D

    def __init__(self,  logicalTables, logicalTableWidths=[],\
                 logicalTableActionWidths=[], logicalMatchDependencyList=[],\
                 logicalActionDependencyList=[], logicalSuccessorDependencyList=[],\
                 matchType=[], names=[]):
        """
        logicalTables(nx1) - list of number of entries indexed by logical table number
        logicalTableWidths(nx1) - list of entry widths indexed by logical table number
        logicalTableActionWidths(nx1) - list of action data widths ..
        logicalMatchDependencyList - list of tuples where (a, b) means table # b depends on a
        logicalActionDependencyList - list of tuples where (a, b) means table # b depends on a
        logicalSuccessorDependencyList - list of tuples where (a, b) means table # b depends on a
        matchType - list of match types (one of 'exact','lpm' or 'ternary') indexed by logical table number
        names - list of table names
        """
        
        # Name variables for easier recognition later.
        if (len(names) == 0):
            names = [str(i) for i in range(len(logicalTables))]
            pass
        self.names = names
        
        ####################################################
        # Sizing limits
        ####################################################

        # Total number of logical tables
        self.MaximumLogicalTables = len(logicalTables)
        # Max number of entries per table
        self.MaximumLogicalSubtablesPerTable = max(logicalTables)
        # Total number of entries; serves as a good upperbound
        self.MaximumLogicalSubtables = self.MaximumLogicalTables * self.MaximumLogicalSubtablesPerTable

        ####################################################
        # Dependencies
        ####################################################
        # logicalMatchDependency[i,j] = 1 means i must come before j
        self.logicalMatchDependencyList = logicalMatchDependencyList
        self.logicalMatchDependency = self.logicalDependencyMatrix(logicalMatchDependencyList)

        # logicalActionDependency[i,j] = 1 means i must come before j
        self.logicalActionDependencyList = logicalActionDependencyList
        self.logicalActionDependency = self.logicalDependencyMatrix(logicalActionDependencyList)

        # logicalSuccessorDependency[i,j] = 1 means i must not come after j
        self.logicalSuccessorDependencyList = logicalSuccessorDependencyList
        self.logicalSuccessorDependency = self.logicalDependencyMatrix(logicalSuccessorDependencyList)

        ####################################################
        # Logical Table sizing/widths/memory
        ####################################################

        # each entry is total number of physical blocks needed 
        # per logical table, disregarding widths
        self.logicalTables = np.matrix(logicalTables).T
        self.logicalTableWidths = np.matrix(logicalTableWidths).T

        
        numTables = self.MaximumLogicalTables
        if len(logicalTableActionWidths) == 0:
            logicalTableActionWidths = [[0] for table in range(numTables)]
            pass
        self.logicalTableActionWidths = logicalTableActionWidths

        self.matchType = matchType
        pass
