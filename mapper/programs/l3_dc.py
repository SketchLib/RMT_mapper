from program import Program as ProgramType
import math
import numpy as np
import logging

class ProgramL3Dc:
        def __init__(self, numberOfEntriesDict = {}):
            table_names = ['port', 'src_mac', 'router_mac', 'host_route', 'lpm_route',\
                               'generate_hash', 'ecmp_select', 'lif', 'lag_select',\
                               'acl', 'eg_set', 'eg_acl', '_condition_1']
            table_widths = {'port': 32, 'src_mac': 64, 'router_mac': 64, 'host_route': 48, 'lpm_route': 48,\
                          'generate_hash': 136, 'ecmp_select': 40, 'lif': 16, 'lag_select': 40, 'acl': 171,\
                          'eg_set': 16, 'eg_acl': 48, '_condition_1': 1}
            action_widths = {'port': [32], 'src_mac': [0], 'router_mac': [0], 'host_route': [24],\
                                 'lpm_route': [24], 'generate_hash': [16], 'ecmp_select': [32], 'lif': [24],\
                                 'lag_select': [16], 'acl': [0], 'eg_set': [112], 'eg_acl': [0], '_condition_1': [0]}
            match_type = {'port': 'exact', 'src_mac': 'exact', 'router_mac': 'exact', 'host_route': 'exact',\
				   'lpm_route': 'lpm', 'generate_hash': 'exact', 'ecmp_select': 'exact', 'lif': 'exact',\
				   'lag_select': 'exact', 'acl': 'lpm', 'eg_set': 'exact', 'eg_acl': 'lpm',\
				   '_condition_1': 'ternary'}
            defaultNumberOfEntriesDict  =\
		{'port': 258, 'src_mac': 1024, 'router_mac': 1024, 'host_route': 1024, 'lpm_route': 1024,\
			 'generate_hash': 1024, 'ecmp_select': 1024, 'lif': 1024, 'lag_select': 1024, 'acl': 1024,\
			 'eg_set': 1024, 'eg_acl': 1024, '_condition_1': 12}
	    num_entries = defaultNumberOfEntriesDict
	    valid = True
	    missingFields = []
	    for field in defaultNumberOfEntriesDict.keys():
		    if field not in numberOfEntriesDict.keys():
			    valid = False
			    missingFields.append(field)
			    pass
		    pass
	    if not valid:
		    logging.warn("Fields %s not in dict, invalid. Using default .. %s" % (missingFields, num_entries))
		    pass
	    else:
		    num_entries = defaultNumberOfEntriesDict
		    pass
	    
            match_dependencies = [('ecmp_select', 'lif'), ('ecmp_select', 'acl'), ('lpm_route', '_condition_1'),\
                                      ('generate_hash', 'ecmp_select'), ('port', 'src_mac'), ('port', 'host_route'),\
                                      ('lif', 'lag_select')]
            action_dependencies = [('router_mac', 'acl'), ('host_route', 'lpm_route'), ('port', 'router_mac')]
            successor_dependencies = [('_condition_1', 'generate_hash')]
            
            
            self.program = ProgramType(logicalTables=[num_entries[t] for t in table_names],\
					       logicalTableWidths=[table_widths[t] for t in table_names],\
					       logicalMatchDependencyList=\
					       [(table_names.index(n1), table_names.index(n2))\
							for (n1, n2) in match_dependencies],\
					       logicalActionDependencyList=\
					       [(table_names.index(n1), table_names.index(n2))\
							for (n1, n2) in action_dependencies],\
					       logicalSuccessorDependencyList=\
					       [(table_names.index(n1), table_names.index(n2))\
							for (n1, n2) in successor_dependencies],\
					       logicalTableActionWidths = [action_widths[t] for t in table_names],\
					       matchType=[match_type[t] for t in table_names],\
					       names = table_names)
            pass
        pass
        
