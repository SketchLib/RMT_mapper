from program import Program as ProgramType
import math
import numpy as np
import logging

IG_Phy_Meta, IG_Smac, IG_Props, IG_Bcast_Storm = 0, 1, 2, 3
IG_ACL1, IG_Router_Mac = 4, 5
Ipv4_Ucast_Host, Ipv4_Ucast_LPM, Ipv4_Mcast, Ipv4_Urpf = 6, 7, 8, 9
Ipv6_Ucast_Host, Ipv6_Ucast_LPM, Ipv6_Mcast, Ipv6_Urpf = 10, 11, 12, 13
Ipv4_Ecmp, Ipv4_Nexthop, Ipv6_Ecmp, Ipv6_Nexthop = 14, 15, 16, 17
IG_Dmac, IG_Agg_Intf, IG_ACL2 = 18, 19, 20
EG_Props, EG_Phy_Meta, EG_ACL1 = 21, 22, 23

numTables = 24

class ProgramL2L3Complex:
    def __init__(self, numberOfEntriesDict = {}):
 
        self.numTables = numTables

        self.t = np.zeros(self.numTables)
        self.w = np.zeros(self.numTables)
        self.aw = [[0] for table in range(self.numTables)]
        self.matchesOn = {}
        self.sets = {}

        self.matchType = {}
        self.names = ["IG_Phy_Meta", "IG_Smac", "IG_Props", "IG_Bcast_Storm", \
                      "IG_ACL1", "IG_Router_Mac", \
                      "Ipv4_Ucast_Host", "Ipv4_Ucast_LPM", "Ipv4_Mcast", "Ipv4_Urpf", \
                      "Ipv6_Ucast_Host", "Ipv6_Ucast_LPM", "Ipv6_Mcast", "Ipv6_Urpf", \
                      "Ipv4_Ecmp", "Ipv4_Nexthop", "Ipv6_Ecmp", "Ipv6_Nexthop", \
                      "IG_Dmac", "IG_Agg_Intf", "IG_ACL2", \
                      "EG_Props", "EG_Phy_Meta", "EG_ACL1"]

        self.setBasicWidths()

        """
        Table 0: IG_Phy_Meta
        M: vlan_id, ig_pif
        A: bd_idx (bridge domain), ig_lif (logical interface) - both metadata
        """
        self.matchesOn[IG_Phy_Meta] = ['vlan_id', 'ig_pif']
        self.sets[IG_Phy_Meta] = ['bd_idx', 'ig_lif']
        self.matchType[IG_Phy_Meta] = 'exact' 
        """
        Table 1: IG_Smac
        Source mac learning.
        """
        self.matchesOn[IG_Smac] = ['bd_idx', 'src_mac', 'ig_lif']
        self.sets[IG_Smac] = []
        self.matchType[IG_Smac] = 'exact'

        """
        Table 2: IG_Props
        Sets vrf_idx and urpf.
        """
        self.matchesOn[IG_Props] = ['bd_idx', 'ig_lif']
        self.sets[IG_Props] = ['vrf_idx', 'urpf', 'bd_acl_label', 'lif_acl_label']
        self.matchType[IG_Props] = 'exact'

        """
        Table 3: IG_Bcast_Storm
        """
        self.matchesOn[IG_Bcast_Storm] = ['ig_pif', 'dst_mac']
        self.sets[IG_Bcast_Storm] = []
        self.matchType[IG_Bcast_Storm] = 'exact'

        """
        Table 4: IG_ACL1
        """
        self.matchesOn[IG_ACL1] = ['ig_pif', 'src_mac', 'dst_mac', 'bd_acl_label', 'lif_acl_label'] # and more
        self.sets[IG_ACL1] = ['drop_code']
        self.matchType[IG_ACL1] = 'ternary' # tcam

        """
        Table 5: IG_Router_Mac
        Decides NTA as IPv4 unicast, IPv4 multicast, IPv6 unicast, IPv6 multicast, or pure L2 packet.
        """
        self.matchesOn[IG_Router_Mac] = ['bd_idx', 'dst_mac', 'eth_type']
        self.sets[IG_Router_Mac] = []
        self.matchType[IG_Router_Mac] = 'exact'

        """
        Table 6: Ipv4_Ucast_Host
        """
        self.matchesOn[Ipv4_Ucast_Host] = ['vrf_idx', 'ipv4_d']
        self.sets[Ipv4_Ucast_Host] = ['ipv4_nexthop_idx', 'ipv4_ecmp_idx']
        self.matchType[Ipv4_Ucast_Host] = 'exact'

        """
        Table 7: Ipv4_Ucast_LPM
        """
        self.matchesOn[Ipv4_Ucast_LPM] = ['vrf_idx', 'ipv4_d']
        self.sets[Ipv4_Ucast_LPM] = ['ipv4_nexthop_idx', 'ipv4_ecmp_idx']
        self.matchType[Ipv4_Ucast_LPM] = 'ternary' # tcam

        """
        Table 8: Ipv4_Mcast
        """
        self.matchesOn[Ipv4_Mcast] = ['vrf_idx', 'ipv4_s', 'ipv4_d', 'bd_idx']
        self.sets[Ipv4_Mcast] = ['mcast_idx']
        self.matchType[Ipv4_Mcast] = 'ternary'

        """
        Table 9: Ipv4_Urpf
        """
        self.matchesOn[Ipv4_Urpf] = ['bd_idx', 'ipv4_s', 'urpf']
        self.sets[Ipv4_Urpf] = []
        self.matchType[Ipv4_Urpf] = 'exact'

        """
        Table 10: Ipv6_Ucast_Host
        """
        self.matchesOn[Ipv6_Ucast_Host] = ['vrf_idx', 'ipv6_d']
        self.sets[Ipv6_Ucast_Host] = ['ipv6_nexthop_idx', 'ipv6_ecmp_idx']
        self.matchType[Ipv6_Ucast_Host] = 'exact'

        """
        Table 11: Ipv6_Ucast_LPM
        """
        self.matchesOn[Ipv6_Ucast_LPM] = ['vrf_idx', 'ipv6_d']
        self.sets[Ipv6_Ucast_LPM] = ['ipv6_nexthop_idx', 'ipv6_ecmp_idx']
        self.matchType[Ipv6_Ucast_LPM] = 'ternary' # tcam

        """
        Table 12: Ipv6_Mcast
        """
        self.matchesOn[Ipv6_Mcast] = ['vrf_idx', 'ipv6_s', 'ipv6_d', 'bd_idx']
        self.sets[Ipv6_Mcast] = ['mcast_idx']
        self.matchType[Ipv6_Mcast] = 'ternary'

        """
        Table 13: Ipv6_Urpf
        """
        self.matchesOn[Ipv6_Urpf] = ['bd_idx', 'ipv6_s', 'urpf']
        self.sets[Ipv6_Urpf] = []
        self.matchType[Ipv6_Urpf] = 'exact'

        """
        Table 14: Ipv4_Ecmp
        """
        self.matchesOn[Ipv4_Ecmp] = ['ipv4_ecmp_idx', 'l3_hash', 'mcast_idx'] # currently forced to match depend mcast
        self.sets[Ipv4_Ecmp] = ['ipv4_nexthop_idx']
        self.matchType[Ipv4_Ecmp] = 'exact'

        """
        Table 15: Ipv4_Nexthop
        """
        self.matchesOn[Ipv4_Nexthop] = ['ipv4_nexthop_idx']
        self.sets[Ipv4_Nexthop] = ['bd_idx', 'src_mac', 'dst_mac']
        self.matchType[Ipv4_Nexthop] = 'exact'

        """
        Table 16: Ipv6_Ecmp
        """
        self.matchesOn[Ipv6_Ecmp] = ['ipv6_ecmp_idx', 'l3_hash', 'mcast_idx'] # currently forced to match depend mcast
        self.sets[Ipv6_Ecmp] = ['ipv4_nexthop_idx']
        self.matchType[Ipv6_Ecmp] = 'exact'

        """
        Table 17: Ipv6_Nexthop
        """
        self.matchesOn[Ipv6_Nexthop] = ['ipv6_nexthop_idx']
        self.sets[Ipv6_Nexthop] = ['bd_idx', 'src_mac', 'dst_mac']
        self.matchType[Ipv6_Nexthop] = 'exact'

        """
        Table 18: IG_Dmac
        """
        self.matchesOn[IG_Dmac] = ['bd_idx', 'dst_mac']
        self.sets[IG_Dmac] = ['eg_lif']
        self.matchType[IG_Dmac] = 'exact'

        """
        Table 19: IG_Agg_Intf
        """
        self.matchesOn[IG_Agg_Intf] = ['eg_lif', 'l2_hash']
        self.sets[IG_Agg_Intf] = ['eg_pif']
        self.matchType[IG_Agg_Intf] = 'exact'

        """
        Table 20: IG_ACL2
        """
        self.matchesOn[IG_ACL2] = ['ipv6_nexthop_idx', 'ipv4_nexthop_idx'] # comes after nexthop setting
        self.sets[IG_ACL2] = ['drop_code']
        self.matchType[IG_ACL2] = 'ternary' # tcam

        """
        Table 21: EG_Props
        """
        self.matchesOn[EG_Props] = ['bd_idx', 'eg_lif']
        self.sets[EG_Props] = ['bd_acl_label', 'lif_acl_label']
        self.matchType[EG_Props] = 'exact'

        """
        Table 22: EG_Phy_Meta
        """
        self.matchesOn[EG_Phy_Meta] = ['eg_pif', 'bd_idx']
        self.sets[EG_Phy_Meta] = ['vlan_id', 'drop_code']
        self.matchType[EG_Phy_Meta] = 'exact'

        """
        Table 23: EG_ACL1
        """
        self.matchesOn[EG_ACL1] = ['bd_idx', 'bd_acl_label', 'lif_acl_label']
        self.sets[EG_ACL1] = ['drop_code']
        self.matchType[EG_ACL1] = 'ternary' # tcam

        
        
        self.setBasicWidths()
        self.setActionDataWidths()
        self.setWidths()
        
        logging.debug("Number of entries per table")
        defaultNumberOfEntriesDict = {'IG_Phy_Meta' : 4000.0, 'IG_Smac' : 128000.0, 'IG_Props' : 4000.0,\
            'IG_Bcast_Storm' : 64.0, 'IG_ACL1' : 8000.0, 'IG_Router_Mac' :\
            1000.0, 'Ipv4_Ucast_Host' : 128000.0, 'Ipv4_Ucast_LPM' :\
            16000.0, 'Ipv4_Mcast' : 32000.0, 'Ipv4_Urpf' : 16000.0,\
            'Ipv6_Ucast_Host' : 128000.0, 'Ipv6_Ucast_LPM' : 16000.0,\
            'Ipv6_Mcast' : 32000.0, 'Ipv6_Urpf' : 16000.0, 'Ipv4_Ecmp' :\
            256.0, 'Ipv4_Nexthop' : 128000.0, 'Ipv6_Ecmp' : 245.0,\
            'Ipv6_Nexthop' : 128000.0, 'IG_Dmac' : 128000.0, 'IG_Agg_Intf'\
            : 64.0, 'IG_ACL2' : 8000.0, 'EG_Props' : 64.0, 'EG_Phy_Meta' :\
            4000.0, 'EG_ACL1' : 16000.0}
        valid = True
        for field in defaultNumberOfEntriesDict.keys():
            if field not in numberOfEntriesDict.keys():
                valid = False
                logging.warn(field + " not in dict, invalid")
                pass
            pass

        if not valid:
            logging.warn("INVALID number of entries, using DEFAULT")
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

        self.md = []
        # no mcast dependency on ecmp.
        self.md = [(IG_Phy_Meta, IG_Props), (IG_Phy_Meta, IG_Smac), (IG_Phy_Meta, IG_Router_Mac), \
            (IG_Smac, IG_ACL1), (IG_Props, IG_ACL1), \
            (IG_Props, Ipv4_Ucast_Host), (IG_Props, Ipv4_Mcast), (IG_Props, Ipv4_Urpf), \
            (IG_Props, Ipv6_Ucast_Host), (IG_Props, Ipv6_Mcast), (IG_Props, Ipv6_Urpf), \
            (Ipv4_Ucast_LPM, Ipv4_Ecmp), (Ipv6_Ucast_LPM, Ipv6_Ecmp),\
            (Ipv4_Ecmp, Ipv4_Nexthop), (Ipv6_Ecmp, Ipv6_Nexthop), \
            (Ipv4_Nexthop, IG_Dmac), (Ipv6_Nexthop, IG_Dmac), \
            (Ipv4_Mcast, IG_Dmac), (Ipv6_Mcast, IG_Dmac), \
            (IG_Dmac, IG_Agg_Intf), (IG_Dmac, EG_Props), \
            (IG_Agg_Intf, EG_Phy_Meta), (IG_Agg_Intf, IG_ACL2), \
            (EG_Props, EG_ACL1), (EG_Phy_Meta, EG_ACL1)]


        logging.debug("Match dependencies")
        for (table2, table1) in self.md:
            logging.debug(str(table2) + " " + self.names[table2] + " <- " + str(table1) + " " + self.names[table1])
            pass
        
        self.ad = [(Ipv4_Ucast_Host, Ipv4_Ucast_LPM), (Ipv6_Ucast_Host, Ipv6_Ucast_LPM)]

        logging.debug("Action dependencies")
        for (table2, table1) in self.ad:
            logging.debug(str(table2) + " " + self.names[table2] + " <- " + str(table1) + " " + self.names[table1])
            pass

        self.setSuccessorDependencies()
        logging.debug("Successor dependencies")
        for (table1, table2) in self.sd:
            logging.debug(self.names[table2] + " <- " + self.names[table1])
            pass

        rmd = [(IG_Smac, Ipv4_Nexthop), (IG_Smac, Ipv6_Nexthop), \
               (IG_Bcast_Storm, Ipv4_Nexthop), (IG_Bcast_Storm, Ipv6_Nexthop)]

        logging.debug("Rev. match dependencies")
        for (table1, table2) in rmd:
            logging.debug(self.names[table2] + " <- " + self.names[table1])
            pass

        self.sd += rmd # Reverse match counts as successor
        
        
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
        self.sd = [(IG_Router_Mac, Ipv4_Ucast_Host), (IG_Router_Mac, Ipv4_Ucast_LPM), \
                   (IG_Router_Mac, Ipv4_Mcast), (IG_Router_Mac, Ipv4_Urpf), \
                   (IG_Router_Mac, Ipv4_Ecmp), (IG_Router_Mac, Ipv4_Nexthop), \
                   (IG_Router_Mac, Ipv6_Ucast_Host), (IG_Router_Mac, Ipv6_Ucast_LPM), \
                   (IG_Router_Mac, Ipv6_Mcast), (IG_Router_Mac, Ipv6_Urpf), \
                   (IG_Router_Mac, Ipv6_Ecmp), (IG_Router_Mac, Ipv6_Nexthop)]
        pass

    def setUseMemory(self):
        useMem = {'sram':[], 'tcam':[]}

        for table in range(self.numTables):
            if self.matchType[table] == 'sram':
                useMem['sram'].append(table)
                pass
            elif self.matchType[table] == 'tcam':
                useMem['tcam'].append(table)
                pass
            else:
                logging.warn("Table " + str(table) + " doesn't have recog. match type")
                pass
            pass
            
        self.useMem = useMem
        pass
            
    def setNumberOfEntries(self):
        t = np.zeros(self.numTables)
         
        t[IG_Phy_Meta] = self.numberOfEntriesDict['IG_Phy_Meta']
        t[IG_Smac] = self.numberOfEntriesDict['IG_Smac']
        t[IG_Props] = self.numberOfEntriesDict['IG_Props']
        t[IG_Bcast_Storm] = self.numberOfEntriesDict['IG_Bcast_Storm']
        t[IG_ACL1] = self.numberOfEntriesDict['IG_ACL1']
        t[IG_Router_Mac] = self.numberOfEntriesDict['IG_Router_Mac']
        t[Ipv4_Ucast_Host] = self.numberOfEntriesDict['Ipv4_Ucast_Host']
        t[Ipv4_Ucast_LPM] = self.numberOfEntriesDict['Ipv4_Ucast_LPM']
        t[Ipv4_Mcast] = self.numberOfEntriesDict['Ipv4_Mcast']
        t[Ipv4_Urpf] = self.numberOfEntriesDict['Ipv4_Urpf']
        t[Ipv6_Ucast_Host] = self.numberOfEntriesDict['Ipv6_Ucast_Host']
        t[Ipv6_Ucast_LPM] = self.numberOfEntriesDict['Ipv6_Ucast_LPM']
        t[Ipv6_Mcast] = self.numberOfEntriesDict['Ipv6_Mcast']
        t[Ipv6_Urpf] = self.numberOfEntriesDict['Ipv6_Urpf']
        t[Ipv4_Ecmp] = self.numberOfEntriesDict['Ipv4_Ecmp']
        t[Ipv4_Nexthop] = self.numberOfEntriesDict['Ipv4_Nexthop']
        t[Ipv6_Ecmp] = self.numberOfEntriesDict['Ipv6_Ecmp']
        t[Ipv6_Nexthop] = self.numberOfEntriesDict['Ipv6_Nexthop']
        t[IG_Dmac] = self.numberOfEntriesDict['IG_Dmac']
        t[IG_Agg_Intf] = self.numberOfEntriesDict['IG_Agg_Intf']
        t[IG_ACL2] = self.numberOfEntriesDict['IG_ACL2']
        t[EG_Props] = self.numberOfEntriesDict['EG_Props']
        t[EG_Phy_Meta] = self.numberOfEntriesDict['EG_Phy_Meta']
        t[EG_ACL1] = self.numberOfEntriesDict['EG_ACL1']

        self.t = t
        pass

    def setBasicWidths(self):

        self.width = {'vlan_id': 12, 'ig_pif': 9, 'src_mac': 48, 'dst_mac': 48, 'eth_type': 16, \
                      'bd_idx': 16, 'vrf_idx': 12, 'ig_lif': 16, \
                      'bd_acl_label': 24, 'lif_acl_label': 24, 'urpf': 2, \
                      'ipv4_s': 32, 'ipv4_d': 32, 'ipv6_s': 64, 'ipv6_d': 64, \
                      'ipv4_nexthop_idx': 16, 'ipv4_ecmp_idx': 16, 'ipv6_nexthop_idx': 16, 'ipv6_ecmp_idx': 16, \
                      'mcast_idx': 16, 'l3_hash': 20, 'l2_hash': 20, 'drop_code': 8, \
                      'eg_lif': 16, 'eg_pif': 9
                    }
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

        # Custom widths
        pass
