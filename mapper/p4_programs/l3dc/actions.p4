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

action drop_packet() {
    modify_field(routing_metadata.drop, 1, 0x1);
    drop();
}

action set_ingress_lif(lif, vrf) {
    modify_field(routing_metadata.i_lif, lif, 0xFFFF);
    modify_field(routing_metadata.vrf, vrf, 0xFFFF);
}

action l2_learn() {
    /* TODO: use the new primtive action for learning */
    modify_field(routing_metadata.learned_i_lif, routing_metadata.i_lif, 0xFFFF);
    modify_field(routing_metadata.learned_mac, ethernet.srcAddr, 0xFFFFFFFFFFFF);
}

action host_route_miss() {
    modify_field(routing_metadata.host_route_miss, 1, 0x1);
}

action lpm_route_miss() {
    modify_field(routing_metadata.lpm_route_miss, 1, 0x1);
}

action get_hash(hash) {
    modify_field(routing_metadata.hash, hash, 0xFFFF);
}

action choose_nhop(o_lif, acl_label) {
    modify_field(routing_metadata.o_lif, o_lif, 0xFFFF);
    modify_field(routing_metadata.i_acl_label, acl_label);
}

action route(ecmp_count, ecmp_base) {
    modify_field(routing_metadata.ecmp_count, ecmp_count);
    modify_field(routing_metadata.ecmp_base, ecmp_base);
    add_to_field(ipv4.ttl, -1);
}

action set_lag_info(lag_base, lag_count) {
    modify_field(routing_metadata.lag_base, lag_base, 0xFF);
    modify_field(routing_metadata.lag_count, lag_count, 0xFF);
}

action choose_port(eg_port) {
    modify_field(routing_metadata.out_port, eg_port, 0xFFFF);
}

action set_egress_info(acl_label, smac, dmac) {
    modify_field(egress_metadata.o_acl_label, acl_label, 0xFFFF);
    modify_field(ethernet.srcAddr, smac, 0xFFFFFFFFFFFF);
    modify_field(ethernet.dstAddr, dmac, 0xFFFFFFFFFFFF);
}

action eg_drop_packet() {
    modify_field(routing_metadata.drop, 1, 0x1);
    drop();
}

action eg_pass() {
    modify_field(routing_metadata.drop, 0, 0x1);
}
