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
        self.logger = logging.getLogger(__name__)
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

    def showProgramInfo(self):

        table_names = self.names

        widths = self.logicalTableWidths
#         {}
#         for i in range(len(self.logicalTableWidths)):
#             widths[table_names[i]] = self.logicalTableWidths[i]
#             pass

        action_widths = self.logicalTableActionWidths
#         {}
#         for i in range(len(self.logicalTableActionWidths)):
#             action_widths[table_names[i]] = self.logicalTableActionWidths[i]
#             pass

        match_types = self.matchType
#         {}
#         for i in range(len(self.matchType)):
#             match_types[table_names[i]] = self.matchType[i]
#             pass

        num_entries = self.logicalTables
#         {}
#         for i in range(len(self.logicalTables)):
#             num_entries[table_names[i]] = self.logicalTables[i]
#             pass

        
        match_dependencies = []
        for a,b in self.logicalMatchDependencyList:
            match_dependencies.append((table_names[a], table_names[b]))
            pass

        action_dependencies = []
        for a,b in self.logicalActionDependencyList:
            action_dependencies.append((table_names[a], table_names[b]))
            pass
        
        successor_dependencies = []
        for a,b in self.logicalSuccessorDependencyList:
            successor_dependencies.append((table_names[a], table_names[b]))
            pass

        numTables = len(table_names);

    #self.logger.info("table_names = {%s}\ntable_widths = {%s}\naction_widths = {%s}\nmatch_types = {%s}\n num_entries={%s}\n num_action_words %s, ingress %s, Select %s" %\
        #   (str(table_names), str(widths), str(action_widths), str(match_types), str(num_entries), str(num_action_words), str(in_ingress), str(select_size)))

        infoStr = "\n";
        infoStr += ("table_names = {%s}\ntable_widths = {%s}\naction_widths = {%s}\nmatch_types = {%s}\n num_entries={%s}\n\n" %\
                        (str(table_names),\
                             ", ".join(["\'%s\': %d" % (table_names[i], widths[i]) for i in range(numTables)]),\
                             ", ".join(["\'%s\': %s" % (table_names[i], str(action_widths[i])) for i in range(numTables)]),\
                             ", ".join(["\'%s\': \'%s\'" % (table_names[i], match_types[i]) for i in range(numTables)]),\
                             ", ".join(["\'%s\': %d" % (table_names[i], num_entries[i]) for i in range(numTables)])))

        depsByName = {"match": match_dependencies, "action": action_dependencies,\
                          "successor": successor_dependencies}
        for name in depsByName:
            infoStr += "%s dependencies: %s\n" % (name, depsByName[name])
            pass

        logging.info(infoStr)

        self.logger.info('%30s%4s%8s%5s%20s' % ('tablename',  'T', '#M-E', 'M-W', 'A-W'))
    
        for i, tablename in enumerate(table_names):
            ostr = '%30s%4s%8d%5d%20s' %\
                (tablename,\
                     match_types[i][0],\
                     num_entries[i],\
                     widths[i],\
                     str(sorted(action_widths[i],\
                                    reverse=True)))
            
            self.logger.info(ostr)
            pass
        pass
            
