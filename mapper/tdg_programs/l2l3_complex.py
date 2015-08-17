from program import Program as ProgramType
import math
import numpy as np
import logging

class ProgramL2L3Complex:
        def __init__(self, numberOfEntriesDict = {}):
            self.logger = logging.getLogger(__name__)

	    table_names = ['IG_Phy_Meta', 'IG_Smac', 'IG_Props', 'IG_Bcast_Storm', 'IG_ACL1', 'IG_Router_Mac', 'Ipv4_Ucast_Host', 'Ipv4_Ucast_LPM', 'Ipv4_Mcast', 'Ipv4_Urpf', 'Ipv6_Ucast_Host', 'Ipv6_Ucast_LPM', 'Ipv6_Mcast', 'Ipv6_Urpf', 'Ipv4_Ecmp', 'Ipv4_Nexthop', 'Ipv6_Ecmp', 'Ipv6_Nexthop', 'IG_Dmac', 'IG_Agg_Intf', 'IG_ACL2', 'EG_Props', 'EG_Phy_Meta', 'EG_ACL1']

	    table_widths = {'IG_Phy_Meta': 21, 'IG_Smac': 80, 'IG_Props': 32, 'IG_Bcast_Storm': 57, 'IG_ACL1': 153, 'IG_Router_Mac': 80, 'Ipv4_Ucast_Host': 44, 'Ipv4_Ucast_LPM': 44, 'Ipv4_Mcast': 92, 'Ipv4_Urpf': 50, 'Ipv6_Ucast_Host': 76, 'Ipv6_Ucast_LPM': 76, 'Ipv6_Mcast': 156, 'Ipv6_Urpf': 82, 'Ipv4_Ecmp': 52, 'Ipv4_Nexthop': 16, 'Ipv6_Ecmp': 52, 'Ipv6_Nexthop': 16, 'IG_Dmac': 64, 'IG_Agg_Intf': 36, 'IG_ACL2': 32, 'EG_Props': 32, 'EG_Phy_Meta': 25, 'EG_ACL1': 64}

	    action_widths = {'IG_Phy_Meta': [16, 16], 'IG_Smac': [0], 'IG_Props': [12, 2, 24, 24], 'IG_Bcast_Storm': [0], 'IG_ACL1': [8], 'IG_Router_Mac': [0], 'Ipv4_Ucast_Host': [16, 16], 'Ipv4_Ucast_LPM': [16, 16], 'Ipv4_Mcast': [16], 'Ipv4_Urpf': [0], 'Ipv6_Ucast_Host': [16, 16], 'Ipv6_Ucast_LPM': [16, 16], 'Ipv6_Mcast': [16], 'Ipv6_Urpf': [0], 'Ipv4_Ecmp': [16], 'Ipv4_Nexthop': [16, 48, 48], 'Ipv6_Ecmp': [16], 'Ipv6_Nexthop': [16, 48, 48], 'IG_Dmac': [16], 'IG_Agg_Intf': [9], 'IG_ACL2': [8], 'EG_Props': [24, 24], 'EG_Phy_Meta': [12, 8], 'EG_ACL1': [8]}

	    match_type = {'IG_Phy_Meta': 'exact', 'IG_Smac': 'exact', 'IG_Props': 'exact', 'IG_Bcast_Storm': 'exact', 'IG_ACL1': 'ternary', 'IG_Router_Mac': 'exact', 'Ipv4_Ucast_Host': 'exact', 'Ipv4_Ucast_LPM': 'ternary', 'Ipv4_Mcast': 'ternary', 'Ipv4_Urpf': 'exact', 'Ipv6_Ucast_Host': 'exact', 'Ipv6_Ucast_LPM': 'ternary', 'Ipv6_Mcast': 'ternary', 'Ipv6_Urpf': 'exact', 'Ipv4_Ecmp': 'exact', 'Ipv4_Nexthop': 'exact', 'Ipv6_Ecmp': 'exact', 'Ipv6_Nexthop': 'exact', 'IG_Dmac': 'exact', 'IG_Agg_Intf': 'exact', 'IG_ACL2': 'ternary', 'EG_Props': 'exact', 'EG_Phy_Meta': 'exact', 'EG_ACL1': 'ternary'}

	    num_entries={'IG_Phy_Meta': 4000, 'IG_Smac': 128000, 'IG_Props': 4000, 'IG_Bcast_Storm': 64, 'IG_ACL1': 8000, 'IG_Router_Mac': 1000, 'Ipv4_Ucast_Host': 128000, 'Ipv4_Ucast_LPM': 16000, 'Ipv4_Mcast': 32000, 'Ipv4_Urpf': 16000, 'Ipv6_Ucast_Host': 128000, 'Ipv6_Ucast_LPM': 16000, 'Ipv6_Mcast': 32000, 'Ipv6_Urpf': 16000, 'Ipv4_Ecmp': 256, 'Ipv4_Nexthop': 128000, 'Ipv6_Ecmp': 245, 'Ipv6_Nexthop': 128000, 'IG_Dmac': 128000, 'IG_Agg_Intf': 64, 'IG_ACL2': 8000, 'EG_Props': 64, 'EG_Phy_Meta': 4000, 'EG_ACL1': 16000}

	    action_dependencies= [('Ipv4_Ucast_Host', 'Ipv4_Ucast_LPM'), ('Ipv6_Ucast_Host', 'Ipv6_Ucast_LPM')]

	    match_dependencies= [('IG_Phy_Meta', 'IG_Props'), ('IG_Phy_Meta', 'IG_Smac'), ('IG_Phy_Meta', 'IG_Router_Mac'), ('IG_Smac', 'IG_ACL1'), ('IG_Props', 'IG_ACL1'), ('IG_Props', 'Ipv4_Ucast_Host'), ('IG_Props', 'Ipv4_Mcast'), ('IG_Props', 'Ipv4_Urpf'), ('IG_Props', 'Ipv6_Ucast_Host'), ('IG_Props', 'Ipv6_Mcast'), ('IG_Props', 'Ipv6_Urpf'), ('Ipv4_Ucast_LPM', 'Ipv4_Ecmp'), ('Ipv6_Ucast_LPM', 'Ipv6_Ecmp'), ('Ipv4_Ecmp', 'Ipv4_Nexthop'), ('Ipv6_Ecmp', 'Ipv6_Nexthop'), ('Ipv4_Nexthop', 'IG_Dmac'), ('Ipv6_Nexthop', 'IG_Dmac'), ('Ipv4_Mcast', 'IG_Dmac'), ('Ipv6_Mcast', 'IG_Dmac'), ('IG_Dmac', 'IG_Agg_Intf'), ('IG_Dmac', 'EG_Props'), ('IG_Agg_Intf', 'EG_Phy_Meta'), ('IG_Agg_Intf', 'IG_ACL2'), ('EG_Props', 'EG_ACL1'), ('EG_Phy_Meta', 'EG_ACL1')]

	    successor_dependencies= [('IG_Router_Mac', 'Ipv4_Ucast_Host'), ('IG_Router_Mac', 'Ipv4_Ucast_LPM'), ('IG_Router_Mac', 'Ipv4_Mcast'), ('IG_Router_Mac', 'Ipv4_Urpf'), ('IG_Router_Mac', 'Ipv4_Ecmp'), ('IG_Router_Mac', 'Ipv4_Nexthop'), ('IG_Router_Mac', 'Ipv6_Ucast_Host'), ('IG_Router_Mac', 'Ipv6_Ucast_LPM'), ('IG_Router_Mac', 'Ipv6_Mcast'), ('IG_Router_Mac', 'Ipv6_Urpf'), ('IG_Router_Mac', 'Ipv6_Ecmp'), ('IG_Router_Mac', 'Ipv6_Nexthop'), ('IG_Smac', 'Ipv4_Nexthop'), ('IG_Smac', 'Ipv6_Nexthop'), ('IG_Bcast_Storm', 'Ipv4_Nexthop'), ('IG_Bcast_Storm', 'Ipv6_Nexthop')]


	    defaultNumberOfEntriesDict = num_entries
	    valid = True
	    missingFields = []
	    for field in defaultNumberOfEntriesDict.keys():
		    if field not in numberOfEntriesDict.keys():
			    valid = False
			    missingFields.append(field)
			    pass
		    pass
	    if not valid:
		    self.logger.warn("Fields %s not in dict, invalid. Using default .. %s" % (missingFields, num_entries))
		    pass
	    else:
		    num_entries = defaultNumberOfEntriesDict
		    pass
	                
            
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
        
