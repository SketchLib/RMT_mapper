from program import Program as ProgramType
import math
import numpy as np
import logging
 
class ProgramL2L3Simple:
        def __init__(self, numberOfEntriesDict = {}):
            self.logger = logging.getLogger(__name__)

	    table_names = ['Routable', 'Acl', 'Smac_Vlan', 'Vrf', 'UrpfV4',\
				    'UrpfV6', 'Igmp_Snooping', 'Check_Ipv6',\
				    'Ipv6_Prefix', 'Check_uCast_Ipv4',\
				    'Ipv4_Forwarding', 'Ipv6_Forwarding',\
				    'Next_Hop', 'Ipv4_Xcast_Forwarding',\
				    'Ipv6_Xcast_Forwarding', 'Dmac_Vlan']
	    
	    table_widths = {'Routable': 82, 'Acl': 160, 'Smac_Vlan': 54, 'Vrf': 66,\
				    'UrpfV4': 50, 'UrpfV6': 146, 'Igmp_Snooping': 50,\
				    'Check_Ipv6': 1, 'Ipv6_Prefix': 64,\
				    'Check_uCast_Ipv4': 4, 'Ipv4_Forwarding': 40,\
				    'Ipv6_Forwarding': 88, 'Next_Hop': 12,\
				    'Ipv4_Xcast_Forwarding': 82,\
				    'Ipv6_Xcast_Forwarding': 146, 'Dmac_Vlan': 66}

	    action_widths = {'Routable': [0], 'Acl': [0], 'Smac_Vlan': [0], 'Vrf': [8],\
				     'UrpfV4': [0], 'UrpfV6': [0], 'Igmp_Snooping': [0],\
				     'Check_Ipv6': [0], 'Ipv6_Prefix': [16],\
				     'Check_uCast_Ipv4': [0], 'Ipv4_Forwarding': [12],\
				     'Ipv6_Forwarding': [12], 'Next_Hop': [48, 48],\
				     'Ipv4_Xcast_Forwarding': [16],\
				     'Ipv6_Xcast_Forwarding': [16], 'Dmac_Vlan': [6]}

	    match_type = {'Routable': 'exact', 'Acl': 'ternary', 'Smac_Vlan': 'exact',\
				   'Vrf': 'exact', 'UrpfV4': 'exact', 'UrpfV6': 'exact', 'Igmp_Snooping': 'ternary', 'Check_Ipv6': 'exact', 'Ipv6_Prefix': 'lpm', 'Check_uCast_Ipv4': 'exact', 'Ipv4_Forwarding': 'lpm', 'Ipv6_Forwarding': 'lpm', 'Next_Hop': 'exact', 'Ipv4_Xcast_Forwarding': 'lpm', 'Ipv6_Xcast_Forwarding': 'lpm', 'Dmac_Vlan': 'exact'}
	    num_entries={'Routable': 64, 'Acl': 80000, 'Smac_Vlan': 160000, 'Vrf': 40000, 'UrpfV4': 160000, 'UrpfV6': 5000, 'Igmp_Snooping': 16000, 'Check_Ipv6': 1, 'Ipv6_Prefix': 1000, 'Check_uCast_Ipv4': 1, 'Ipv4_Forwarding': 160000, 'Ipv6_Forwarding': 5000, 'Next_Hop': 41250, 'Ipv4_Xcast_Forwarding': 16000, 'Ipv6_Xcast_Forwarding': 1000, 'Dmac_Vlan': 160000}

	    action_dependencies= []
	    match_dependencies= [('Ipv6_Prefix', 'Ipv6_Forwarding'), ('Next_Hop', 'Dmac_Vlan'), ('Ipv6_Forwarding', 'Next_Hop'), ('Ipv4_Forwarding', 'Next_Hop')]
	    successor_dependencies= [('Routable', 'Vrf'), ('Routable', 'UrpfV6'), ('Routable', 'Igmp_Snooping'), ('Routable', 'Check_Ipv6'), ('Check_Ipv6', 'Ipv6_Prefix'), ('Check_Ipv6', 'Check_uCast_Ipv4'), ('Ipv6_Prefix', 'UrpfV6'), ('Ipv6_Prefix', 'Igmp_Snooping'), ('Ipv6_Prefix', 'Ipv6_Xcast_Forwarding'), ('Check_uCast_Ipv4', 'Ipv4_Forwarding'), ('Check_uCast_Ipv4', 'UrpfV4'), ('Check_uCast_Ipv4', 'Ipv4_Xcast_Forwarding'), ('Smac_Vlan', 'Next_Hop'), ('Acl', 'Next_Hop'), ('Routable', 'Next_Hop')]
	    


            defaultNumberOfEntriesDict  = num_entries
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
        
