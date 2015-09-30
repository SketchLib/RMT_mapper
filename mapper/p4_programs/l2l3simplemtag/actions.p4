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

action on_hit() {
}
action on_miss() {
}
action nop() {
}

action set_vrf(vrf) {
    modify_field(hop_metadata.vrf, vrf);
}

action set_ipv6_prefix_ucast(ipv6_prefix){
    modify_field(hop_metadata.ipv6_prefix, ipv6_prefix);
}

action set_ipv6_prefix_xcast(ipv6_prefix){
    modify_field(hop_metadata.ipv6_prefix, ipv6_prefix);
}

action set_next_hop(dst_index) {
    modify_field(hop_metadata.next_hop_index, dst_index);
}

action set_ethernet_addr(smac, dmac) {
    modify_field(ethernet.srcAddr, smac);
    modify_field(ethernet.dstAddr, dmac);
}

action set_multicast_replication_list(mc_index) {
    modify_field(hop_metadata.mcast_grp, mc_index);
}

action set_urpf_check_fail() {
    modify_field(hop_metadata.urpf_fail, 1);
}

action urpf_check_fail() {
    set_urpf_check_fail();
    drop();
}

action set_egress_port(e_port) {
    modify_field(standard_metadata.egress_spec, e_port);
}

action set_mtag_egress(egress_spec) {
    modify_field(standard_metadata.egress_spec, egress_spec);
}

action strip_mtag(egress_spec) {
    modify_field(vlan_tag_[0].etherType, mtag.etherType);
    remove_header(mtag);
    modify_field(hop_metadata.was_mtagged, 1);
}

action add_mtag(up1, up2, down1, down2) {
    add_header(mtag);
    /* Copy VLAN etherType to mTag
    modify_field(mtag.etherType, vlan_tag_[0].etherType);
    /* Set VLAN's etherType to signal mTag */
    modify_field(vlan_tag_[0].etherType, VLAN_MTAG);

    modify_field(mtag.up1, up1);
    modify_field(mtag.up2, up2);
    modify_field(mtag.down1, down1);
    modify_field(mtag.down2, down2);

    /* Set the destination egress port as well */
    set_mtag_egress(up1);
}

action action_drop(drop_reason) {
    modify_field(hop_metadata.drop_reason, drop_reason);
    drop();
}
