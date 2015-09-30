/*
Copyright (c) 2015-2016 by The Board of Trustees of the Leland
Stanford Junior University.  All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


 Author: Lisa Yan (yanlisa@stanford.edu)
*/

/* Table 1:  Routable
 * Matches on VLAN, port #, DMAC and Ethertype to determine if this frame
 * is routable (addressed to the router).
 * Set Routable (field or metadata)
 */
table routable {
    reads {
        vlan_tag_[0] : valid;
        vlan_tag_[0].vid : exact;
        standard_metadata.ingress_port : exact;
        ethernet.dstAddr : exact;
        ethernet.etherType : exact;
    }
    actions {
        on_hit;
        on_miss;
    }
    size : ROUTABLE_SIZE;
}

/* Table 2:  SMAC/VLAN
 * Matches on the SMAC/VLAN from the frame (not affected by routing)
 */
table smac_vlan {
    reads {
        ethernet.srcAddr : exact;
        standard_metadata.ingress_port : exact;
    }
    actions {
        nop; /* FIX */
    }
    size : SMAC_VLAN_SIZE;
}

/* Table 3:  VRF
 * Matches {VLAN, SMAC} produces a 8-bit VRF
 * Set Vrf (field or metadata)
 */
table vrf {
    reads {
        vlan_tag_[0] : valid;
        vlan_tag_[0].vid : exact;
        ethernet.srcAddr : exact;
        standard_metadata.ingress_port : exact;
    }
    actions {
        set_vrf;
    }
    size : VRF_SIZE;
}

/* Table 4: Check IPv6
 * Checks if IPv6 header is valid.
 */
table check_ipv6 {
    reads {
        ipv6 : valid;
    }
    actions {
        on_hit;
        on_miss;
    }
    size : CHECK_IPV6_SIZE;
}

/* Table 5:  IPv6 Prefix
 * Matches on Dest IPv6[127:64], produces a 16-bit prefix
 * Set Ipv6_Prefix (field or metadata)
 */
table ipv6_prefix {
    reads {
        ipv6.dstAddr : lpm;
    }
    actions {
        set_ipv6_prefix_ucast;
        set_ipv6_prefix_xcast;
    }
    size : IPv6_PREFIX_SIZE;
}

/* Table 6: IPv4 Ucast
 * checks if an address falls into xcast category
 * and redirects to xcast table if needed.
 */
table check_ucast_ipv4 {
    reads {
        ipv4.dstAddr : exact;
    }
    actions {
        nop; /* FIX */
    }
    size : CHECK_UCAST_IPV4_SIZE;
}

/* Table 7:  IPv4 Forwarding
 * Match on {VRF, DestIPv4}, produce a NextHop Index
 * Ucast only.
 */
table ipv4_forwarding {
    reads {
        hop_metadata.vrf : exact; 
        ipv4.dstAddr : lpm;
    }
    actions {
        set_next_hop;
    }
    size : IPV4_FORWARDING_SIZE;
}

/* Table 8:  IPv6 Forwarding
 * Match on {VRF, v6prefix, destipv6[63:0]}, produce a NextHop Index
 */
table ipv6_forwarding {
    reads {
        hop_metadata.vrf : exact;
        hop_metadata.ipv6_prefix : exact;
        ipv6.dstAddr : lpm;
    }
    actions {
        set_next_hop;
    }
    size : IPV6_FORWARDING_SIZE;
}

/* Table 9: Next Hop
 * Use NextHop Index to set src/dst MAC addresses.
 */
table next_hop {
    reads {
        hop_metadata.next_hop_index : exact;
    }
    actions {
        set_ethernet_addr;
    }
    size : NEXT_HOP_SIZE;
}

/* Table 10:  Multicast IPv4 Forwarding
 * Match on {VLAN, DestIPv4, SourceIPv4}, produce a multicast replication list
 * , flood set, and/or a PIM assert
 */
table ipv4_xcast_forwarding {
    reads {
        vlan_tag_[0].vid : exact;
        ipv4.dstAddr : lpm;
        ipv4.srcAddr : lpm;
        standard_metadata.ingress_port : exact;
    }
    actions {
        set_multicast_replication_list;
    }
    size : IPV4_XCAST_FORWARDING_SIZE;
}

/* Table 11:  Multicast IPv6 Forwarding
 * Match on {VLAN, DestIPv6, SourceIPv6}, produce a multicast replication list
 * , flood set, and/or a PIM assert
 */
table ipv6_xcast_forwarding {
    reads {
        vlan_tag_[0].vid : exact;
        ipv6.dstAddr : lpm;
        ipv6.srcAddr : lpm;
        standard_metadata.ingress_port : exact;
    }
    actions {
        set_multicast_replication_list;
    }
    size : IPV6_XCAST_FORWARDING_SIZE;
}

/* Table 12:  uRPF IPv4 Check
 * Match on {VLAN, SourceIPv4}, action is NOP
 * Default action is to drop
 */
table urpf_v4 {
    reads {
        vlan_tag_[0].vid : exact;
        standard_metadata.ingress_port : exact;
        ipv4.srcAddr : exact;
    }
    actions {
        urpf_check_fail;
        nop;
    }
    size : URPF_V4_SIZE;
}

/* Table 13:  uRPF IPv6 Check
 * Match on {VLAN, SourceIPv6}, action is NOP
 * Default action is to drop
 */
table urpf_v6 {
    reads {
        vlan_tag_[0].vid : exact;
        standard_metadata.ingress_port : exact;
        ipv6.srcAddr : exact;
    }
    actions {
        urpf_check_fail;
        nop;
    }
    size : URPF_V6_SIZE;
}

/* Table 14:  IGMP Snooping
 */
table igmp_snooping {
    reads {
        ipv4.dstAddr : lpm;
        vlan_tag_[0].vid : exact;
        standard_metadata.ingress_port : exact;
    }
    actions {
        nop; /* FIX */
    }
    size : IGMP_SNOOPING_SIZE;
}

/* Table 15:  DMAC/VLAN
 * Matches on the DMAC/VLAN either from the frame, or from the result of the
 * route (NextHop DMAC/VLAN)
 */
table dmac_vlan {
    reads {
        ethernet.dstAddr : exact;
        vlan_tag_[0].vid : exact;
        standard_metadata.ingress_port : exact;
    }
    actions {
        on_miss;
        set_egress_port;
    }
    size : DMAC_VLAN_SIZE;
}

/* Table 16:  ACLs
 *   Generically match on a set of ingress conditions
 *   Generically associate some action (permit/deny/police/mirror/trap/SetField/
 *   etc.)
 * ????????????????????? only ipv4??
 */
table acl {
    reads {
        ipv4.srcAddr : lpm;
        ipv4.dstAddr : lpm;
        ethernet.srcAddr : exact;
        ethernet.dstAddr : exact;
    }
    actions {
        action_drop;
    }
    size : ACL_SIZE;
}

/*
 * Table 17: Source_Check
 */
table source_check {
    reads {
        mtag : valid;
        standard_metadata.ingress_port : exact;
    }
    actions {
        strip_mtag;
        action_drop;
        nop;
    }
}

/*
 * Table 18: mTag
 */
table mtag_table {
    reads {
        ethernet.dstAddr : exact;
        vlan_tag_[0].vid : exact;
        vlan_tag_[0].etherType : exact;  
    }
    actions {
        add_mtag;
        nop;
    }
}

/*
 * Table 19: EG_mTag_Check
 */
table eg_mtag_check {
    reads {
        mtag : valid;
        vlan_tag_[0].vid : exact;
        standard_metadata.egress_port : exact;
    }
    actions {
        action_drop;
        nop;
    }
}
