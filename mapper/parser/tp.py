"""
[get|show]ProgramInfo() returns|displays program info- table names, widths, action widths, match types, num entries
indexed by table number in a format suitable for initializing a Program from mapper.programs.program
"""

import os
import subprocess
import argparse
import logging

import p4_hlir.hlir.p4 as p4
import p4_hlir.hlir.dependencies as dependencies
import p4_hlir.hlir.table_dependency as table_dependency

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
hlir=None

logger.debug("CHECKING")
from collections import OrderedDict, defaultdict



defaultMatch = {'width':32, 'match_type':'exact', 'action_widths':[0], 'num_entries':1024, 'num_action_words':1, 'fixed_action_data_per_stage':False}
defaultCondition = {'width':1, 'match_type':'gw', 'action_widths':[0], 'num_entries':12, 'num_action_words':1, 'fixed_action_data_per_stage':False}

def get_tables(graphs): # {
    defaultStr = ""
    def round_to(width, div):
        numDivs = width/div
        remainder = width%div
        if remainder == 0:
            return numDivs * div
        else:
            return numDivs * div + div
        pass
   
    def get_one_field_width(field, _type):
        if _type == p4.p4_match_type.P4_MATCH_VALID:
            return 1;
        else:
            return field.width
         
    def get_field_width(match_fields, name):
        # TODO(lav): Fix bugs in preprocess, compiler when width for table is 0.
        # Then remove max(1,..)
        if len(match_fields) == 0:
            return None
        else:
            tot = 0
            for (field,_type,mask) in match_fields :
                tot += get_one_field_width(field, _type)
            return tot;

    def get_match_type(match_fields):
        if len(match_fields) == 0:
            return None
        else:
            types = [_type for (field,_type,mask) in match_fields]
            pass

        if len(types) == 0:
            logger.warning("Match fields: %s" % str(match_fields) +\
                             "WARNING!! No types to match on")
            return None
        elif p4.p4_match_type.P4_MATCH_TERNARY in types:
            return 'ternary'
        elif p4.p4_match_type.P4_MATCH_RANGE in types:
            return 'ternary'
        elif p4.p4_match_type.P4_MATCH_LPM in types:
            return 'lpm'
        elif p4.p4_match_type.P4_MATCH_EXACT in types:
            return 'exact'
        elif p4.p4_match_type.P4_MATCH_VALID in types:
            return 'exact'
        else:
            logger.warning("ERROR!! invalid match type")
            return None
        pass

    def get_action_width(actions):
        # TODO(lav): how to assign action memory
        # if multiple parameters, possibly different widths for an action.
        # possibly more than one actions for an entry
        # different actions for different entries in a table
        # also which of these arg_width is for a p4_table_entry_data
        # vs for a p4_field
        # TODO(lav): Divide by zero error in preprocess if instead of max
        # had just .. = [[sum(..]] and one of the widths was 0 like [[0,32],[..]]
        if len(actions) == 0:
            return 0
        width = [[arg_width for arg_width in p4_action.signature_widths]\
                     for p4_action in actions]
                      
        total_width = [sum([arg_width for arg_width in action_args\
                                if arg_width is not None])\
                           for action_args in width]
        return total_width

    tablesInGraph = {}
    for graphName in graphs:
        tablesInGraph[graphName] = [table.name for table in graphs[graphName]._nodes.values()]
        logger.info("%d tables in %s control flow: %s" % (len(tablesInGraph[graphName]), graphName, tablesInGraph[graphName]))
        pass


    p4MatchTables = [p4_table_name\
                       for p4_table_name, p4_table in hlir.p4_tables.items()]
    logger.info("%d tables in p4 tables: %s" % (len(p4MatchTables), p4MatchTables))

    p4ConditionalTables = ["_condition_%d" % index\
                                  for index in range(1,len(hlir.p4_conditional_nodes)+1)]
    logger.info("%d tables in p4 conditional nodes: %s" % (len(p4ConditionalTables), p4ConditionalTables))

    tablesInAllGraphs = []
    for graphName in graphs:
        tablesInAllGraphs += tablesInGraph[graphName]
        pass
    
    tablesNotInControlFlow = [table for table in p4MatchTables+p4ConditionalTables if\
                                  table not in tablesInAllGraphs]
    logger.info("%d p4 tables / conditional nodes not in control flow: %s" %\
                     (len(tablesNotInControlFlow), tablesNotInControlFlow))
                                  
    # Add table only if it's in a control graph
    tables = [{'name':p4_table_name,\
                   'width':get_field_width(p4_table.match_fields, p4_table_name),\
                   'action_widths':get_action_width(p4_table.actions),\
                   'match_type':get_match_type(p4_table.match_fields),\
                   'num_entries':p4_table.max_size,\
                   'fixed_action_data_per_stage':None, \
                   'ingress': p4_table_name in tablesInGraph["ingress"], \
                   'hlir':p4_table, \
                   'select_size':0, \
                   'next_table_count': len(p4_table.next_),\
                   'action_count': len(p4_table.actions),\
                   'num_action_words':None}
                  for p4_table_name, p4_table in hlir.p4_tables.items()\
                  if p4_table_name in tablesInAllGraphs]

    for p4_table_name, p4_table in hlir.p4_tables.items():
        if p4_table_name in tablesInAllGraphs:
            fields = [(field.name, get_one_field_width(field, _type), round_to(get_one_field_width(field,_type), 8))\
                          for field,_type,mask in p4_table.match_fields]
            totalWidth = sum([width for name,width,rwidth in fields])
            totalRWidth = sum([rwidth for name,width,rwidth in fields])
            logger.info("Table %s has width: %d, rounded width: %d for fields: %s" %\
                             (p4_table_name, totalWidth, totalRWidth, fields))
            pass
        pass

    for p4_table_name, p4_table in hlir.p4_tables.items():
        if p4_table_name in tablesInAllGraphs:
            actionSignatures = [[(action.signature[i], action.signature_widths[i])\
                    for i in range(len(action.signature))]\
                                    for action in p4_table.actions]
            logger.info("Table %s has action data: %s" %\
                             (p4_table_name, actionSignatures))
            pass
        pass

    # Add tables only if it's in a control graph
    # Assuming condition tables in ingress, egress graph numbered in order they appear
    # in the list. Need to find a better way.
    tables += [{'name': hlir_name,\
                    'width': defaultCondition['width'],\
                    'action_widths': defaultCondition['action_widths'],\
                    'match_type':defaultCondition['match_type'],\
                    'num_entries':defaultCondition['num_entries'],\
                    'fixed_action_data_per_stage':defaultCondition['fixed_action_data_per_stage'],\
                    'hlir': hlir.p4_conditional_nodes[hlir_name], \
                    'ingress': hlir_name in tablesInGraph["ingress"], \
                    'select_size':0, \
                    'next_table_count': 2, \
                    'action_count': 2,\
                    'num_action_words':defaultCondition['num_action_words']} \
                    for (_, hlir_name) in enumerate(hlir.p4_conditional_nodes) ]
    logger.warning("All condition tables have default settings: %s" % defaultCondition)

    for table in tables:
        logger.debug('TABLE %s %s' % (table['hlir'].name, str(table)))

    #for table in tables:
    #    if table['name'] in tablesInEgressGraph:
    #        table['ingress'] = False
    # index in collection, to identify condition e.g., _condition_1_ etc.

    return tables
# } get-tables

def get_lists(tables):
    lists = {}
    tables_with_default = {}
    for k in tables[0].keys():
        lists[k] = []
        tables_with_default[k] = []
        pass

    for table in tables:
        for k in table.keys():
            value = table[k]
            if value == None:
                value = defaultMatch[k]
                tables_with_default[k].append(table['name'])
                pass
            lists[k].append(value)
            pass
        pass
    logger.info("total width %d" % (sum(lists['width'])))
    for k in tables_with_default.keys():
        if len(tables_with_default[k]) > 0:
            logger.warning("WARNING!! Can't get %s for %s, setting to %s" %\
                             (k, tables_with_default[k], defaultMatch[k]))
            pass
        pass

    return lists['name'], lists['width'], lists['action_widths'], lists['match_type'],\
        lists['num_entries'], lists['num_action_words'], lists['fixed_action_data_per_stage'],\
        lists['ingress'], lists['select_size'], lists['next_table_count'], lists['action_count']
    

def get_dependencies(graphs):
    deps = {}
    types = table_dependency.Dependency._types

    for graphName in graphs:
        logger.info("DEPENDENCIES FROM %s TABLE GRAPH", graphName)
        for type_ in types.keys():
            deps[types[type_]] = [(table.name, dependency.to.name)\
                                      for table in graphs[graphName]._nodes.values()\
                                      for dependency in table.next_tables.values()\
                                      if dependency.type_ == type_]
            logger.info("%s: %s" % (types[type_], deps[types[type_]]))
            pass


        pass
    return deps

def unique_list(l, idfun=None):
    seen = {}
    result = []
    if idfun is None:
        def idfun(x): return x
        pass
    for item in l:
        marker = idfun(item)
        if marker in seen: continue
        seen[marker] = 1
        result.append(item)
        pass
    return result

    
def getProgramInfo(input_hlir):
    global hlir
    hlir = input_hlir
    logging.getLogger().setLevel(logging.DEBUG)

    graphs = {}
    graphs["ingress"] = table_dependency.rmt_build_table_graph_ingress(hlir)
    #graphs["egress"] = table_dependency.rmt_build_table_graph_egress(hlir)
    
    for graphName in graphs:
        graphs[graphName].transitive_reduction()
        pass

    deps = get_dependencies(graphs)
    # deps is {string: [(string, string)]} -- mapping dependency type to list
    # of (from,to) pairs of table names

    tables = get_tables(graphs)
    # tables is [{string: any}] -- one map for each table
    table_names = [t['name'] for t in tables]
    logger.info("tables-names: %s" % [(i, t['name']) for (i,t) in enumerate(tables)])


    # table_names, widths etc. only for action tables, not condition tables
    # each action table must be associated with some condition table now,
    # TODO(lav): solver should use condition table widths for input crossbar
    # ignoring that for now
    # TODO(): assuming every action table has a corresponding condition table
    # cuz if (..) then (..) else (..) is the only way to execute an action table?

    depsByName = {}
    for _type in deps.keys():
        depsByName[_type] = unique_list(\
            [(table1, table2)\
                 for table1, table2 in deps[_type]])
        pass


    # Need to update list of tables, for (table1, table2) in INDEX dependencies
    # check that * table1 has no action data, table2 has ??
    # update table1's action data to be fixed, xx entries of width xx
    # delete table2 from dict

    
    new_tables = [t for t in tables]
    logger.info("Tables input to compiler: %s" % [t['name'] for t in new_tables])
    new_tables_names = [t['name'] for t in new_tables]
    logger.info("new-tables-names: %s" % [(i, t['name']) for (i,t) in enumerate(new_tables)])

     
    table_names, widths, action_widths, match_types, num_entries,\
        num_action_words, fixed_action_data_per_stage, in_ingress,\
        select_size, next_table_count, action_count = get_lists(new_tables)

    programInfo = {}
    programInfo["table_names"] = table_names
    programInfo["widths"] = widths
    programInfo["action_widths"] = action_widths
    programInfo["match_types"] = match_types
    programInfo["num_entries"] = num_entries

    def getDepsByIndex(depsByN):
        depsByIndex = []
        for pair in depsByN:
            index0 = table_names.index(pair[0])
            index1 = table_names.index(pair[1])
            depsByIndex.append((index0, index1))
            pass        
        return depsByIndex

    def getUnique(listOfDeps):
        uniqueList = []
        for deps in listOfDeps:
            for pair in deps:
                if pair not in uniqueList:
                    uniqueList.append(pair)
                    pass
                pass
            pass
        return uniqueList
    
    programInfo["matchDependencies"] = getDepsByIndex(depsByName["MATCH"])


    allActionDeps = getDepsByIndex(depsByName["ACTION"])
    actionDeps = []
    for pair in allActionDeps:
        if pair not in programInfo["matchDependencies"]:
            actionDeps.append(pair)
            pass
        pass
    
    programInfo["actionDependencies"] = actionDeps
    
    uniqueSuccessorDeps = getUnique([depsByName["SUCCESSOR"],depsByName["PREDICATION"],depsByName["REVERSE_READ"]])
    successorDeps = []
    for pair in uniqueSuccessorDeps:
        if pair not in programInfo["matchDependencies"] and pair not in programInfo["actionDependencies"]:
            successorDeps.append(pair)
            pass
        pass
    
    programInfo["successorDependencies"] = getDepsByIndex(successorDeps)

    print "UNIQUE SUCCESOR DEPS: %s" % uniqueSuccessorDeps
    print "SUCCESSOR DEPS NOT IN MATCH OR ACTION: %s" % successorDeps
    

    
    programInfo["num_action_words"] = num_action_words
    programInfo["fixed_action_data_per_stage"] = fixed_action_data_per_stage
    programInfo["in_ingress"] = in_ingress
    programInfo["select_size"] = select_size
    programInfo["next_table_count"] = next_table_count
    programInfo["action_count"] = action_count
    programInfo["depsByName"] = depsByName
    
    return programInfo

def showProgramInfo(input_hlir):
    pi = getProgramInfo(input_hlir)

    table_names, widths, action_widths, match_types, num_entries,\
        num_action_words, fixed_action_data_per_stage, in_ingress,\
        select_size, next_table_count, action_count =\
        pi["table_names"], pi["widths"], pi["action_widths"], pi["match_types"], pi["num_entries"],\
        pi["num_action_words"], pi["fixed_action_data_per_stage"], pi["in_ingress"],\
        pi["select_size"], pi["next_table_count"], pi["action_count"]

    numTables = len(table_names);
    #logger.info("table_names = {%s}\ntable_widths = {%s}\naction_widths = {%s}\nmatch_types = {%s}\n num_entries={%s}\n num_action_words %s, ingress %s, Select %s" %\
     #   (str(table_names), str(widths), str(action_widths), str(match_types), str(num_entries), str(num_action_words), str(in_ingress), str(select_size)))

    infoStr = "\n";
    infoStr += ("table_names = {%s}\ntable_widths = {%s}\naction_widths = {%s}\nmatch_types = {%s}\n num_entries={%s}\n\n" %\
                    (str(table_names),\
                         ", ".join(["\'%s\': %d" % (table_names[i], widths[i]) for i in range(numTables)]),\
                         ", ".join(["\'%s\': %s" % (table_names[i], str(action_widths[i])) for i in range(numTables)]),\
                         ", ".join(["\'%s\': \'%s\'" % (table_names[i], match_types[i]) for i in range(numTables)]),\
                         ", ".join(["\'%s\': %d" % (table_names[i], num_entries[i]) for i in range(numTables)])))

    depsByName = pi["depsByName"]
    for name in depsByName:
        infoStr += "%s dependencies: %s\n" % (name, depsByName[name])
        pass

    logging.info(infoStr)

    logger.info('%30s%4s%4s%4s%4s%8s%8s%5s%8s%20s' % ('tablename', 'T', 'IE', 'nxt','#A', 'S-size', '#M-E', 'M-W', '#A-E', 'A-W'))
    
    for i, tablename in enumerate(table_names):
        ostr = '%30s%4s%4s%4d%4d%8d%8d%5d%8d%20s' %\
               (tablename,\
                match_types[i][0],\
                'I' if in_ingress[i] else 'E',\
                next_table_count[i], \
                action_count[i],\
                select_size[i],\
                num_entries[i],\
                widths[i],\
                num_action_words[i],\
                str(sorted(action_widths[i],\
                reverse=True)))

        logger.info(ostr)

def main():
    pass
