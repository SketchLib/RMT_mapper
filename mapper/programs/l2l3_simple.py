from program import Program as ProgramType
import math
import numpy as np
import logging

Routable, Acl, Smac_Vlan, Vrf, UrpfV4, UrpfV6, Igmp_Snooping, Check_Ipv6,\
  Ipv6_Prefix, Check_uCast_Ipv4, Ipv4_Forwarding, Ipv6_Forwarding,\
  Next_Hop, Ipv4_Xcast_Forwarding, Ipv6_Xcast_Forwarding,\
  Dmac_Vlan\
  = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15

class ProgramL2L3Simple:
    def __init__(self, numberOfEntriesDict={}):
 
        self.numTables = Dmac_Vlan + 1

        self.t = np.zeros(self.numTables)
        self.w = np.zeros(self.numTables)
        self.aw = [[0] for table in range(self.numTables)]
        self.matchesOn = {}
        self.sets = {}
        self.useMem = {}
        self.matchType = {}
        self.names = ["Routable",\
                          "Acl",\
                          "Smac_Vlan",\
                          "Vrf",\
                          "UrpfV4",\
                          "UrpfV6",\
                          "Igmp_Snooping",\
                          "Check_Ipv6",\
                          "Ipv6_Prefix",\
                          "Check_uCast_Ipv4",\
                          "Ipv4_Forwarding",\
                          "Ipv6_Forwarding",\
                          "Next_Hop",\
                          "Ipv4_Xcast_Forwarding",\
                          "Ipv6_Xcast_Forwarding",\
                          "Dmac_Vlan"]
        
        self.setBasicWidths()
        """
        Vlans 100s to 1000s
        Smac 64K
        Dmac 64K
        Sipv4, Dipv4 100s to 300K
        Vlan-Smac = 10K say 1000 to 100,000 (say 10-100 Smacs per Vlan)
        Vlan-Dmac = 10K
        Vrf 10 (not sure)
        Vrf-Dipv4 = 10K say 1000 to 10,000 (say 100-1000 Dipv4s per Vlan)
        Ipv4_Xcast = 100 (100-1000 how many xcast groups?)
        Ipv6_Xcast = 100
        Vlan-Sipv4 = 10K (say 10-100 Sipv4s per Vlan)
        Dmac-Vlan-Next_Hop_Id 10K
        """
        
        """
        Table 0:  Routable
        Matches on VLAN, port #, DMAC and Ethertype to determine if this frame
        is routable (addressed to the router).
        Set Routable (field or metadata)
        """

        self.matchesOn[Routable] = ['Vlan','In_Pif','Dmac','Ethertype']
        self.sets[Routable] = []
        self.matchType[Routable] = 'exact'
        """
        Table 11:  SMAC/VLAN
        Matches on the SMAC/VLAN from the frame (not affected by routing)
        """

        self.matchesOn[Smac_Vlan] = ['Smac', 'In_Pif']
        self.sets[Smac_Vlan] = []
        self.matchType[Smac_Vlan] = 'exact'


        """
        Table 2:  VRF
        Matches {VLAN, SMAC} produces a 8-bit VRF
        Set Vrf (field or metadata)
        """

        self.matchesOn[Vrf] = ['Vlan', 'Smac', 'In_Pif']
        self.sets[Vrf] = ['Vrf']
        self.matchType[Vrf] = 'exact'
        
        """
        Table 2:  IPv6 Prefix
        Matches on Dest IPv6[127:64], produces a 16-bit prefix
        Set Ipv6_Prefix (field or metadata)
        """

        self.matchesOn[Check_Ipv6] = ['Is_Ipv6']
        self.sets[Check_Ipv6] = []
        self.matchType[Check_Ipv6] = 'exact'

        # width 64 bits
        self.matchesOn[Ipv6_Prefix] = ['Dipv6']
        self.sets[Ipv6_Prefix] = ['V6Prefix']
        self.matchType[Ipv6_Prefix] = 'lpm'
        
        """
        Table 3:  IPv4 Forwarding
        Match on {VRF, DestIPv4}, produce a NextHop Index
        """

        # width 4 bits, IPv4 multicast begins with 1111
        self.matchesOn[Check_uCast_Ipv4] = ['Dipv4']
        self.sets[Check_uCast_Ipv4] = []
        self.matchType[Check_uCast_Ipv4] = 'exact'
        
        self.matchesOn[Ipv4_Forwarding] = ['Vrf','Dipv4']
        self.sets[Ipv4_Forwarding] = ['Next_Hop_Index']
        self.matchType[Ipv4_Forwarding] = 'lpm'
        
        self.matchesOn[Next_Hop] = ['Next_Hop_Index']
        self.sets[Next_Hop] = ['Smac', 'Dmac']
        self.matchType[Next_Hop] = 'exact'
        
        """
        Table 4:  IPv6 Forwarding
        Match on {VRF, v6prefix, DestIPv6[63:0]}, produce a NextHop Index
        """

        # width 64b of Dipv6? + ..
        self.matchesOn[Ipv6_Forwarding] = ['Vrf','V6Prefix','Dipv6']
        self.sets[Ipv6_Forwarding] = ['Next_Hop_Index']
        self.matchType[Ipv6_Forwarding] = 'lpm'
                
        """
        Table 5:  Multicast IPv4 Forwarding
        Match on {VLAN, DestIPv4, SourceIPv4}, produce a multicast replication list
        , flood set, and/or a PIM assert
        """
        
        self.matchesOn[Ipv4_Xcast_Forwarding] = ['Vlan','In_Pif', 'Dipv4','Sipv4']
        self.sets[Ipv4_Xcast_Forwarding] = ['Multicast_Replication_List']
        self.matchType[Ipv4_Xcast_Forwarding] = 'lpm'
    
        """
        Table 6:  Multicast IPv6 Forwarding
        Match on {VLAN, DestIPv4, SourceIPv4}, produce a multicast replication list
        , and/or a PIM assert
        """

        self.matchesOn[Ipv6_Xcast_Forwarding] = ['Vlan', 'In_Pif', 'Dipv6','Sipv6']
        self.sets[Ipv6_Xcast_Forwarding] = ['Multicast_Replication_List']
        self.matchType[Ipv6_Xcast_Forwarding] = 'lpm'
        
        """
        Table 8:  uRPF Checks
        Match on {VLAN, SourceIP}, action is NOP
        Default action is to drop
        """

        self.matchesOn[UrpfV4] = ['Vlan', 'In_Pif', 'Sipv4']
        self.sets[UrpfV4] = ['Urpf_Check_Fail']
        self.matchType[UrpfV4] = 'exact' 

        self.matchesOn[UrpfV6] = ['Vlan', 'In_Pif', 'Sipv6']
        self.sets[UrpfV6] = ['Urpf_Check_Fail']
        self.matchType[UrpfV6] = 'exact' 

        """
        Table 9:  ACLs
        Generically match on a set of ingress conditions
        Generically associate some action (permit/deny/police/mirror/trap/SetField/
        etc.)
        """

        self.matchesOn[Acl] = ['Sipv4','Dipv4','Smac','Dmac']
        self.sets[Acl] = []
        self.matchType[Acl] = 'ternary'
        """
        Table 10:  DMAC/VLAN
        Matches on the DMAC/VLAN either from the frame, or from the result of the
        route (NextHop DMAC/VLAN)
        """

        self.matchesOn[Dmac_Vlan] = ['Dmac', 'Vlan', 'In_Pif']
        self.sets[Dmac_Vlan] = ['Eg_Pif']
        self.matchType[Dmac_Vlan] = 'exact'
        
        """
        Table 12:  IGMP Snooping
        Matches on {Dest IPv4, VLAN} and a control bit saying that this frame is
        IPv4 multicast and was not forwarded by the FFU
        """

        self.matchesOn[Igmp_Snooping] = ['Dipv4', 'Vlan', 'In_Pif']
        self.sets[Igmp_Snooping] = []
        self.matchType[Igmp_Snooping] = 'ternary'
        
        self.setBasicWidths()
        self.setActionDataWidths()
        self.setWidths()
        
        logging.debug("Number of entries per table")
        defaultNumberOfEntriesDict = {'Acl':80000.0, 'Ipv4_Forwarding': 160000, 'Smac_Vlan': 160000, 'Routable': 64, 'Ipv6_Prefix': 1000,\
                                                        'Ipv6_Forwarding': 5000, 'Ipv4_Xcast_Forwarding': 16000, 'Ipv6_Xcast_Forwarding': 1000}
        valid = True
        for field in defaultNumberOfEntriesDict.keys():
            if field not in numberOfEntriesDict.keys():
                valid = False
                logging.debug(field + " not in dict, invalid")
                pass
            pass

        if not valid:
            logging.debug("INVALID number of entries, using DEFAULT")
            self.numberOfEntriesDict = defaultNumberOfEntriesDict
            pass
        else:
            self.numberOfEntriesDict = numberOfEntriesDict
        logging.debug("number of entries: " + str(self.numberOfEntriesDict))

        self.setNumberOfEntries()
        string = ""
        for table in range(self.numTables):
            string += str(table) +\
              ") t["+self.names[table]+"] = " + str(self.t[table]) +\
              " # matchesOn " + str(self.matchesOn[table]) +\
              " width " + str(self.w[table]) +\
              " # sets " + str(self.sets[table]) +\
              " action data width " + str(self.aw[table]) + "\n"
            pass
        logging.debug(string)
        
        flows = {}
        flows['Ipv4'] = [Smac_Vlan, Acl, Routable, UrpfV4, Ipv4_Forwarding, Next_Hop, Dmac_Vlan]
        flows['Ipv4_Xcast'] = [Smac_Vlan, Acl, Routable, Igmp_Snooping, Ipv4_Xcast_Forwarding]
        flows['Ipv6'] = [Smac_Vlan, Acl, Routable, Ipv6_Prefix, UrpfV6, Ipv6_Forwarding, Next_Hop, Dmac_Vlan]
        flows['Ipv6_Xcast'] = [Smac_Vlan, Acl, Routable, Ipv6_Prefix, Ipv6_Xcast_Forwarding]
        flows['Switching_Xcast'] = [Smac_Vlan, Acl, Routable, Igmp_Snooping]
        flows['Switching'] = [Smac_Vlan, Acl, Routable, Dmac_Vlan]
        
        self.md = []
        # Tables appear in imperative program order
        self.md = [(flows[fl][index1], flows[fl][index2])\
                   for fl in flows \
                   for index1 in range(len(flows[fl]))\
                   for index2 in range(len(flows[fl]))\
                   if index1 < index2 and \
                   any(f in self.matchesOn[flows[fl][index2]] for f in self.sets[flows[fl][index1]])]
        self.md = list(set(self.md))

        logging.debug("Match dependencies")
        for (table2, table1) in self.md:
            logging.debug(str(table2) + " " + self.names[table2] + " <- " + str(table1) + " " + self.names[table1])
            pass

        self.ad = []
        self.ad = [(flows[fl][index1], flows[fl][index2])\
                   for fl in flows \
                   for index1 in range(len(flows[fl]))\
                   for index2 in range(len(flows[fl]))\
                   if index1 < index2 and \
                   any(f in self.sets[flows[fl][index2]]\
                       for f in self.sets[flows[fl][index1]]) and \
                   (flows[fl][index1], flows[fl][index2]) not in self.md]

        self.ad = list(set(self.ad))
        logging.debug("Action dependencies")
        for (table2, table1) in self.ad:
            logging.debug(str(table2) + " " + self.names[table2] + " <- " + str(table1) + " " + self.names[table1])
            pass

        self.setSuccessorDependencies()

        # e.g., Acl matches on ingress Dmac, and routing changes this
        # so Acl can't come after routing
        rmd = [(flows[fl][index1], flows[fl][index2])\
                   for fl in flows \
                   for index1 in range(len(flows[fl]))\
                   for index2 in range(len(flows[fl]))\
                   if index1 < index2 and \
                   any(f in self.sets[flows[fl][index2]]\
                   for f in self.matchesOn[flows[fl][index1]]) and \
                   (flows[fl][index1], flows[fl][index2]) not in self.sd and\
                   (flows[fl][index1], flows[fl][index2]) not in self.md and\
                   (flows[fl][index1], flows[fl][index2]) not in self.ad]
        
        rmd = list(set(rmd))

        logging.debug("Rev. match dependencies")
        for (table2, table1) in rmd:
            logging.debug(self.names[table2] + " <- " + self.names[table1])
            pass

        logging.debug("Successor dependencies")
        for (table1, table2) in self.sd:
            logging.debug(self.names[table2] + " <- " + self.names[table1])
            pass

        self.sd += rmd
                
        self.program = ProgramType(logicalTables=self.t,\
                                       logicalTableWidths=self.w,\
                                       logicalMatchDependencyList=self.md,\
                                       logicalActionDependencyList=self.ad,\
                                       logicalSuccessorDependencyList=self.sd,\
                                       logicalTableActionWidths = self.aw,\
                                       matchType=self.matchType,\
                                       names = self.names)
                            

        pass

    def setSuccessorDependencies(self):
        sd = [(Routable, Vrf), (Routable, UrpfV6),\
              (Routable, Igmp_Snooping), (Routable, Check_Ipv6),\
              (Check_Ipv6, Ipv6_Prefix),\
              (Check_Ipv6, Check_uCast_Ipv4),\
              (Ipv6_Prefix, UrpfV6),\
              (Ipv6_Prefix, Ipv6_Forwarding),\
              (Ipv6_Prefix, Igmp_Snooping),\
              (Ipv6_Prefix, Ipv6_Xcast_Forwarding),\
              (Check_uCast_Ipv4, Ipv4_Forwarding),\
              (Check_uCast_Ipv4, UrpfV4),\
              (Check_uCast_Ipv4, Ipv4_Xcast_Forwarding)]
        self.sd = [pair for pair in sd if pair not in self.md and pair not in self.ad]
        pass
            
    def setNumberOfEntries(self):
        t = np.zeros(self.numTables)

        t[Acl] = self.numberOfEntriesDict['Acl']  # R: Each Stage x Table y has 4K entries
        t[Ipv4_Forwarding] = self.numberOfEntriesDict['Ipv4_Forwarding'] # R: Host routing has 128K exact, LPM routing has 16K                
        t[Smac_Vlan] = self.numberOfEntriesDict['Smac_Vlan'] # R: bd_idx, src_mac, ig_lif_idx -> src_mac_miss .., 128K entries

        t[Routable] = self.numberOfEntriesDict['Routable']  # matches on Vlan, In_Pif, Dmac to see if frame addresses to this router (aka is routable) .. #In_Pif ??        
        t[Ipv6_Prefix] = self.numberOfEntriesDict['Ipv6_Prefix'] 
        t[Ipv6_Forwarding] = self.numberOfEntriesDict['Ipv6_Forwarding']
        t[Ipv4_Xcast_Forwarding] = self.numberOfEntriesDict['Ipv4_Xcast_Forwarding'] # R:vrf_idx, ipv4_sa, ipv4_da, bd_idx .. -> 16b mcast_idx has 16K src, 16K shared
        t[Ipv6_Xcast_Forwarding] = self.numberOfEntriesDict['Ipv6_Xcast_Forwarding']

        t[Vrf] = t[Ipv4_Forwarding]/4  # R: For Bd_idx -> vrf_idx table, 4K entries is a minimum .. for 16K LP Routing
        t[UrpfV4] = t[Ipv4_Forwarding] # R: same as routing tables
        t[UrpfV6] = t[Ipv6_Forwarding] # R: same as routing tables

        t[Dmac_Vlan] = t[Smac_Vlan]   # R: cd_idx, dst_mac -> eg_lif_idx has 128K entries
        t[Igmp_Snooping] = t[Ipv4_Xcast_Forwarding] # Wiki: IGMP operates between the client computer and a local multicast router ??

        
        t[Check_Ipv6] = 1
        t[Check_uCast_Ipv4] = 1
        t[Next_Hop] = (t[Ipv4_Forwarding]+t[Ipv6_Forwarding])/4 # 1/4 as many next hops as dest. prefixes?
        self.t = t
        pass

    def setBasicWidths(self):
        self.width = {\
                      'Is_Ipv6': 1,\
                      'Is_Ipv4': 1, 'V6Prefix': 16, 'Dmac': 48,\
                      'In_Pif': 6, 'Ethertype': 16, 'Vlan': 12,\
                      'Smac': 48, 'Sipv6': 128, 'Dipv6': 128,\
                      'Sipv4': 32, 'Dipv4': 32, 'Vrf': 8,\
                      'Multicast_Replication_List': 16, 'Vrid': 8, 'Urpf_Check_Fail':1,\
                      'Eg_Pif': 6, 'Next_Hop_Index': 12}
        pass
    
    def setActionDataWidths(self):
        aw = [[0] for table in range(self.numTables)]
        for table in range(self.numTables):
            aw[table] = [self.width[f] for f in self.sets[table] if self.width[f] > 1]
            if len(aw[table]) == 0:
                aw[table] = [0]
                pass
            pass
        self.aw = aw

        pass
    
    def setWidths(self):
        w = np.zeros(self.numTables)
        
        fields = {}
        for table in range(self.numTables):
            for f in self.matchesOn[table]:
                fields[f] = 1
                pass
            pass

        logging.debug(fields)
        
        for table in range(self.numTables):
            w[table] = sum([self.width[f] for f in self.matchesOn[table]])
            pass
        self.w = w

        self.w[Ipv6_Prefix] = 64 # Matches on Dest IPv6[127:64]
        self.w[Check_uCast_Ipv4] = 4 # IPv4 multicast begins with 1111
        self.w[Ipv6_Forwarding] = self.width['Vrf']+self.width['V6Prefix']+64
        self.w[Ipv6_Xcast_Forwarding] = 64*2 + self.width['Vlan'] + self.width['In_Pif'] # V6, V6, Vlan, In_Pif
        # Match on {VRF, v6prefix, DestIPv6[63:0]}
        pass
