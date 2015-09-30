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

action action_drop(drop_reason) {
    modify_field(hop_metadata.drop_reason, drop_reason);
    drop();
}
