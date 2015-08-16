from program import Program as ProgramType
import math
import numpy as np

Routable, Acl, Smac_Vlan, UrpfV4, Ipv4_Forwarding, Ipv4_Xcast_Forwarding, \
Igmp_Snooping, Strip_Mtag, mTag, Dmac_Vlan,\
  Egress_Check=\
0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10



# Smac_Vlan matches on Smac, Vlan and learns Smac, Vlan -Ig_pif 
# Routable matches on In_Pif, Vlan, Dmac, Ethertype and sets Is_Routable, drop_source
# (Source_Check function) (Checks only pkts from Agg have mTag)

# If Is_Routable = Routable (dstmac = this router's mac and ethtype = IP)
#  If Is_IpV4_Ucast
#   UrpfV4 (exact) matches on Is_.., Vlan, In_Pif, Sipv4 and sets Urpf_Check_Fail
#   Ipv4_Forwarding (LPM) matches on Vlan, Dipv4 and sets Dmac
#  If Is_Ipv4_Xcast_Forwarding
#   Ipv4_XCast_Forwarding matches on (Is_.., Is_..) Vlan, Dipv4, Sipv4, In_Pif
#  and sets Multicast Replication List
#   Igmp_Snooping matches on (Is..), Vlan, Dipv4, In_Pif
# else if Is_Routable = Mtag (dstmac = .. and ethtype = mTag)
#  Strip_Mtag matches on Is_Routable, In_Pif
# else if Is_Routable = Switching (dstmac = not this router's mac and ethtype = IP)
#  nothing ..
# ---
# At this point, packet has Ethernet/Vlan/Ip and dstmac of next hop after this router

# Dmac_Vlan matches on Is_Routable, Vlan, Dmac and sets Eg_Pif
# If no match in Dmac_Vlan and Is_Routable = Switching 
#  mTag matches on Vlan, Dmac and sets mTag, Vlan, Eg_Pif
# ---
# At this point, packet has Eg_Pif and dstmac of next hop (if mTag, then of next hop after mTag path)

# Egress_Check matches on In_Pif, Is_Routable, Eg_Pif and drops 
# (if packet that was originally mTagged or from Agg are going to Agg)
# 
# Acl matches on Is_Ipv4, Sipv4, Dipv4, Smac, Dmac and drops

class ProgramDdMtag:
    def __init__(self, numberOfEntriesDict={}):
 
        self.numTables = 11


        self.t = np.zeros(self.numTables)
        self.w = np.zeros(self.numTables)
        self.aw = [[0] for table in range(self.numTables)]
        self.matchesOn = {}
        self.sets = {}

        self.matchType = {}

        self.namesToNum = {"Routable":Routable,\
                          "Acl":Acl,\
                          "Smac_Vlan":Smac_Vlan,\
                          "UrpfV4":UrpfV4,\
                          "Igmp_Snooping":Igmp_Snooping,\
                          "Strip_Mtag":Strip_Mtag,\
                          "Ipv4_Forwarding":Ipv4_Forwarding,\
                          "Ipv4_Xcast_Forwarding":Ipv4_Xcast_Forwarding,\
                          "Dmac_Vlan":Dmac_Vlan, \
                          "mTag":mTag, \
                          "Egress_Check": Egress_Check}
        self.names = sorted(self.namesToNum.keys(), key=lambda k:self.namesToNum[k])
        print self.names
                          
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

        # mTags should only be seen on ports connected to core switches (strip_mtag)
        # packets from core should stay local (egress_check)

        self.matchesOn = {\
            Routable : ['Vlan','In_Pif','Dmac','Vlan.Ethertype'],\
                Smac_Vlan: ['Smac', 'In_Pif'],\
                Ipv4_Forwarding: ['Is_Routable','Is_Ipv4_Ucast', 'Vlan','Dipv4'],\
                Ipv4_Xcast_Forwarding: ['Is_Routable', 'Is_Ipv4_Xcast','Vlan', 'In_Pif',\
                                            'Dipv4','Sipv4'],\
                UrpfV4: ['Is_Ipv4_Ucast', 'Is_Routable','Vlan', 'In_Pif', 'Sipv4'],\
                Igmp_Snooping: ['Dipv4', 'Vlan', 'In_Pif', 'Is_Ipv4_Xcast'],\
                Strip_Mtag: ['Is_Routable', 'In_Pif'],\
                Dmac_Vlan: ['Is_Routable', 'Dmac', 'Vlan', 'In_Pif'],\
                mTag: ['Dmac', 'Vlan'],\
                Egress_Check: ['In_Pif', 'Is_Routable', 'Eg_Pif'],\
                Acl: ['Is_Ipv4','Sipv4','Dipv4','Smac','Dmac']\
                }
        
        self.sets = {\
            Routable: ['Is_Routable', 'Drop_Source_Check'], Smac_Vlan: [], Ipv4_Forwarding: ['Smac', 'Dmac'],\
            Ipv4_Xcast_Forwarding: ['Multicast_Replication_List'],\
                UrpfV4: ['Urpf_Check_Fail'], Igmp_Snooping: [],\
                Strip_Mtag: [],\
                mTag: ['Eg_Pif', 'mTag', 'Vlan.Ethertype'], Dmac_Vlan: ['Eg_Pif'],\
                Egress_Check: ['Drop_Mtag'], Acl: ['Drop_Acl']\
            }

        self.matchType = {\
            Routable: 'mapper', Smac_Vlan: 'exact', Ipv4_Forwarding: 'lpm',\
            Ipv4_Xcast_Forwarding: 'lpm', UrpfV4: 'exact', Igmp_Snooping: 'exact',\
                Strip_Mtag: 'exact', mTag: 'exact', Dmac_Vlan: 'exact',\
                Egress_Check: 'exact', Acl: 'ternary'\
                }

        
        self.setBasicWidths()
        self.setActionDataWidths()
        self.setWidths()
        
        print "Number of entries per table"
        # STRIP_MTAG 2, IDENTIFY_PORT PORT_COUNT, LOCAL_SWITCHING NUM_HOSTS?, MTAG 20K, EGRESS_CHECK PORT_COUNT
        PORT_COUNT = 64
        V4_XCAST = 500
        V4_LPM = 4000
        V4_HOSTS = 32000
        MTAGGED = 20000

        # LPM: 16K to Host 128K, Urpf=LPM
        # Smac 128K etc., ACL: 8K
        # mTag for all non local hosts? total hosts: V4_LPM x V4_HOSTS 20K? 4000x5

        defaultNumberOfEntriesDict = {\
            'Acl':1000.0, 'Ipv4_Forwarding': V4_LPM, 'Smac_Vlan': V4_HOSTS,\
                'Routable': PORT_COUNT, 'Ipv4_Xcast_Forwarding': V4_XCAST,\
                'Strip_Mtag': PORT_COUNT, 'mTag': MTAGGED}
                # 'Local_Switching': V4_HOSTS, 'Egress_Check': PORT_COUNT * PORT_COUNT}

        # defaultNumberOfEntriesDict = {'Acl':1000.0, 'Ipv4_Forwarding': 4000, 'Smac_Vlan': 4000, 'Routable': 64, 'Ipv6_Prefix': 500,\
        #                                                 'Ipv6_Forwarding': 500, 'Ipv4_Xcast_Forwarding': 1000, 'Ipv6_Xcast_Forwarding': 2, \
        # 'Source_Check': 64, 'mTag': 200, 'EG_mTag_Check':2000, 'UrpfV4': 2000, 'UrpfV6': 250}
        valid = True
        for field in defaultNumberOfEntriesDict.keys():
            if field not in numberOfEntriesDict.keys():
                valid = False
                print field + " not in dict, invalid"
                pass
            pass

        if not valid:
            print "INVALID number of entries, using DEFAULT"
            self.numberOfEntriesDict = defaultNumberOfEntriesDict
            pass
        else:
            self.numberOfEntriesDict = numberOfEntriesDict
        print "number of entries: ", 
        print self.numberOfEntriesDict
        
        self.setNumberOfEntries()
        
        for table in range(self.numTables):
            print table,
            print ") t["+self.names[table]+"] = " + str(self.t[table]),
            print " # matchesOn " + str(self.matchesOn[table]),
            print " width " + str(self.w[table]),
            print " # sets " + str(self.sets[table]),
            print " action data width " + str(self.aw[table])
            
            pass

        flows = {}
        flows['Routable_v4'] = [Smac_Vlan, Acl, Routable, UrpfV4, Ipv4_Forwarding, Dmac_Vlan, Egress_Check]
        flows['Routable_v4X'] = [Smac_Vlan, Acl, Routable, UrpfV4, Igmp_Snooping, Ipv4_Xcast_Forwarding]
        flows['Switching_v4'] = [Smac_Vlan, Acl, Routable, Dmac_Vlan, mTag, Egress_Check]
        flows['Switching_v4X'] = [Smac_Vlan, Acl, Routable, Igmp_Snooping]
        flows['mTag'] = [Smac_Vlan, Acl, Routable, Strip_Mtag, Dmac_Vlan, Egress_Check]

        # flows['Ipv4'] = [Smac_Vlan, Acl, Routable, UrpfV4, Ipv4_Forwarding, Strip_Mtag, Local_Switching, Dmac_Vlan, Egress_Check]
        # flows['Ipv4_Xcast'] = [Smac_Vlan, Acl, Routable, Igmp_Snooping, Ipv4_Xcast_Forwarding]
        # flows['Switching_Xcast'] = [Smac_Vlan, Acl, Routable, Igmp_Snooping]
        # flows['Switching'] = [Smac_Vlan, Acl, Routable, Strip_Mtag, Local_Switching, Dmac_Vlan, Egress_Check]
        # flows['Mtagging_FromAgg'] = [Smac_Vlan, Acl, Routable, Strip_Mtag, Local_Switching, Dmac_Vlan, Egress_Check]
        # flows['Mtagging_FromEdge'] = [Smac_Vlan, Acl, Routable, Strip_Mtag, Local_Switching, mTag, Dmac_Vlan, Egress_Check]

        # Add a s.d. Local_Switching <- mTag .. if no mapping found in Local_Switching, then mTag

        self.md = []
        # Tables appear in imperative program order
        self.md = [(flows[fl][index1], flows[fl][index2])\
                   for fl in flows \
                   for index1 in range(len(flows[fl]))\
                   for index2 in range(len(flows[fl]))\
                   if index1 < index2 and \
                   any(f in self.matchesOn[flows[fl][index2]] for f in self.sets[flows[fl][index1]])]
        self.md = list(set(self.md))
        # self.md.append((Ipv4_Xcast_Forwarding, Dmac_Vlan))
        # self.md.append((Ipv6_Xcast_Forwarding, Dmac_Vlan))
        # self.md += [(mTag, EG_mTag_Check), (Dmac_Vlan, EG_mTag_Check)]

        print "Match dependencies"
        for (table2, table1) in self.md:
            print str(table2) + " " + self.names[table2] + " <- " + str(table1) + " " + self.names[table1]
            pass

        # TODO(lav): How to compute action dependencies, control flow and table order..
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
        #self.ad += [(Source_Check, mTag)]
        print "Action dependencies"
        for (table2, table1) in self.ad:
            print str(table2) + " " + self.names[table2] + " <- " + str(table1) + " " + self.names[table1]
            pass

        self.setSuccessorDependencies()
        edge = (Dmac_Vlan, mTag)
        if edge not in self.ad and edge not in self.md:
            self.sd += [edge]
            pass

        # e.g., Acl matches on ingress Dmac, and routing changes this
        # so Acl can't come after routing
        rmd = [(flows[fl][index1], flows[fl][index2])\
                   for fl in flows \
                   for index1 in range(len(flows[fl]))\
                   for index2 in range(len(flows[fl]))\
                   if index1 < index2 and \
                   any(f in self.sets[flows[fl][index2]]\
                       for f in self.matchesOn[flows[fl][index1]]) and \
                   (flows[fl][index1], flows[fl][index2]) not in self.md and\
                   (flows[fl][index1], flows[fl][index2]) not in self.ad and\
                   (flows[fl][index1], flows[fl][index2]) not in self.sd ]
        
        rmd = list(set(rmd))

        print "Rev. match dependencies"
        for (table2, table1) in rmd:
            print self.names[table2] + " <- " + self.names[table1]
            pass

        print "Successor dependencies"
        for (table1, table2) in self.sd:
            print self.names[table2] + " <- " + self.names[table1]
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
        self.sd = []
        pass
            
    def setNumberOfEntries(self):                                                        
        t = np.zeros(self.numTables)
        # matches on Vlan, In_Pif, Dmac to see if frame addresses to this router (aka is routable) .. #In_Pif ??        
        t[Routable] = self.numberOfEntriesDict['Routable']  
        t[Acl] = self.numberOfEntriesDict['Acl'] 
        t[Smac_Vlan] = self.numberOfEntriesDict['Smac_Vlan']
        t[UrpfV4] = self.numberOfEntriesDict['Ipv4_Forwarding']
        t[Ipv4_Forwarding] = self.numberOfEntriesDict['Ipv4_Forwarding']  
        t[Ipv4_Xcast_Forwarding] = self.numberOfEntriesDict['Ipv4_Xcast_Forwarding'] 
        t[Igmp_Snooping] = self.numberOfEntriesDict['Ipv4_Xcast_Forwarding'] # Wiki: IGMP operates between the client computer and a local multicast router ??
        t[Strip_Mtag] = self.numberOfEntriesDict['Strip_Mtag'] 
        t[mTag] = self.numberOfEntriesDict['mTag']
        t[Dmac_Vlan] = self.numberOfEntriesDict['Smac_Vlan']   
        t[Egress_Check] = self.numberOfEntriesDict['Strip_Mtag']**2
        self.t = t
        pass

    def setBasicWidths(self):
        self.width = {\
                      'Is_Routable': 2,  'Is_Ipv4_Ucast': 1, 'Is_Ipv4_Xcast':1,\
                      'Is_Ipv4': 1, 'Dmac': 48,\
                      'In_Pif': 6, 'Vlan.Ethertype': 16, 'Vlan': 12,\
                      'Smac': 48,\
                      'Sipv4': 32, 'Dipv4': 32,\
                      'Multicast_Replication_List': 16, 'Urpf_Check_Fail':1,\
                      'Eg_Pif': 6, \
                          'Drop_Mtag': 2, 'Drop_Acl': 1, 'Drop_Source_Check':2,\
                          'mTag': 48}

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

        print fields
        
        for table in range(self.numTables):
            w[table] = sum([self.width[f] for f in self.matchesOn[table]])
            pass
        self.w = w
        pass
