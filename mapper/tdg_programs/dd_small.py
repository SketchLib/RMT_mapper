from program import Program as ProgramType
import math
import numpy as np
import logging

class ProgramDdSmall:
        def __init__(self, numberOfEntriesDict = {}):
            self.logger = logging.getLogger(__name__)


	    table_names = ['Routable', 'Acl', 'Smac_Vlan', 'Vrf', 'UrpfV4', 'UrpfV6', 'Igmp_Snooping', 'Ipv6_Prefix', 'Ipv4_Forwarding', 'Ipv6_Forwarding', 'Ipv4_Xcast_Forwarding', 'Ipv6_Xcast_Forwarding', 'Dmac_Vlan']

	    table_widths = {'Routable': 82, 'Acl': 161, 'Smac_Vlan': 54, 'Vrf': 66, 'UrpfV4': 52, 'UrpfV6': 148, 'Igmp_Snooping': 51, 'Ipv6_Prefix': 64, 'Ipv4_Forwarding': 42, 'Ipv6_Forwarding': 88, 'Ipv4_Xcast_Forwarding': 84, 'Ipv6_Xcast_Forwarding': 140, 'Dmac_Vlan': 66}

	    action_widths = {'Routable': [0], 'Acl': [0], 'Smac_Vlan': [0], 'Vrf': [8], 'UrpfV4': [0], 'UrpfV6': [0], 'Igmp_Snooping': [0], 'Ipv6_Prefix': [16], 'Ipv4_Forwarding': [48, 48], 'Ipv6_Forwarding': [48, 48], 'Ipv4_Xcast_Forwarding': [16], 'Ipv6_Xcast_Forwarding': [16], 'Dmac_Vlan': [6]}

	    match_type = {'Routable': 'mapper', 'Acl': 'ternary', 'Smac_Vlan': 'exact', 'Vrf': 'exact', 'UrpfV4': 'exact', 'UrpfV6': 'exact', 'Igmp_Snooping': 'exact', 'Ipv6_Prefix': 'lpm', 'Ipv4_Forwarding': 'lpm', 'Ipv6_Forwarding': 'lpm', 'Ipv4_Xcast_Forwarding': 'lpm', 'Ipv6_Xcast_Forwarding': 'lpm', 'Dmac_Vlan': 'exact'}

	    num_entries={'Routable': 64, 'Acl': 1000, 'Smac_Vlan': 4000, 'Vrf': 1000, 'UrpfV4': 4000, 'UrpfV6': 500, 'Igmp_Snooping': 1000, 'Ipv6_Prefix': 500, 'Ipv4_Forwarding': 4000, 'Ipv6_Forwarding': 500, 'Ipv4_Xcast_Forwarding': 1000, 'Ipv6_Xcast_Forwarding': 2, 'Dmac_Vlan': 4000}

	    action_dependencies= []
	    match_dependencies= [('Ipv4_Forwarding', 'Dmac_Vlan'), ('Routable', 'Ipv6_Prefix'), ('Routable', 'Ipv6_Xcast_Forwarding'), ('Routable', 'UrpfV6'), ('Routable', 'Ipv4_Xcast_Forwarding'), ('Routable', 'UrpfV4'), ('Routable', 'Ipv6_Forwarding'), ('Routable', 'Ipv4_Forwarding'), ('Ipv6_Forwarding', 'Dmac_Vlan'), ('Ipv6_Prefix', 'Ipv6_Forwarding'), ('Ipv4_Xcast_Forwarding', 'Dmac_Vlan'), ('Ipv6_Xcast_Forwarding', 'Dmac_Vlan')]
	    successor_dependencies= [('Smac_Vlan', 'Ipv4_Forwarding'), ('Acl', 'Ipv4_Forwarding'), ('Acl', 'Ipv6_Forwarding'), ('Smac_Vlan', 'Ipv6_Forwarding')]


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
        
