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

table port {
    reads {
        standard_metadata.ingress_port : exact;
    }
    actions {
        drop_packet;   /* default */
        set_ingress_lif;
    }
    min_size : 258;
    max_size : 258;
}

table src_mac {
    reads {
        ethernet.srcAddr : exact;
        routing_metadata.i_lif : exact;
    }
    actions {
        l2_learn; /* default */
    }
    min_size : 1024;
    max_size : 1024;
}

table router_mac {
    reads {
        ethernet.etherType : exact;
        ethernet.dstAddr : exact;
    }
    actions {
        drop_packet;   /* default */
    }
    min_size : 1024;
    max_size : 1024;
}

table host_route {
    reads {
        routing_metadata.vrf : exact;
        ipv4.dstAddr : exact;
    }
    actions {
        host_route_miss; /* default */
        route;
    }
    min_size : 8192;
    max_size : 8192;

}

table lpm_route {
    reads {
        routing_metadata.vrf : exact;
        ipv4.dstAddr : lpm;
    }
    actions {
        lpm_route_miss; /* default */
        route;
    }
    min_size : 16384;
    max_size : 16384;
}

table generate_hash {
    reads {
        ipv4.dstAddr : exact;
        ipv4.srcAddr : exact;
        ipv4.protocol : exact;
        udp.srcPort : exact;
        udp.dstPort : exact;
        tcp.srcPort : exact;
        tcp.dstPort : exact;
    }
    actions {
        get_hash;
    }
}

table ecmp_select {
    reads {
        routing_metadata.ecmp_base : exact; /* TODO: change this to "base" */
        routing_metadata.ecmp_count : exact; /* TODO: change this to "range" */
        routing_metadata.hash : exact; /* TODO: change this to "offset" */
    }
    actions {
        choose_nhop;
    }
    min_size : 65536;
    max_size : 65536;
}

table lif {
    reads {
        routing_metadata.o_lif : exact;
    }
    actions {
        set_lag_info;
    }
}

table lag_select {
    reads {
        routing_metadata.lag_base : exact;
        routing_metadata.lag_count : exact;
        routing_metadata.hash : exact;
    }
    actions {
        choose_port;
    }
    min_size : 4096;
    max_size : 4096;
}

/* Needs to be tuple match which can have any of the fields     */
/* specified as actual values, masked or ranges                 */
/* dst/src mac, dst/src IP, protocol, tcp flags, src/dst port,  */
/* vrf, bd/vlan, nhop ip, ing_lif/port, l2/l3 hit/miss, ...     */
/* Below is just an example of src/dst ip                       */

table acl {
    reads {
        routing_metadata.i_acl_label : lpm;
        routing_metadata.vrf : lpm;
        ipv4.dstAddr : lpm;
        ipv4.srcAddr : lpm;
        ipv4.protocol : lpm;
        udp.srcPort : lpm;
        udp.dstPort : lpm;
        tcp.ecn : lpm;
        tcp.srcPort : lpm;
        tcp.dstPort : lpm;
    }
    actions {
        drop_packet;
    }
    min_size : 4096;
    max_size : 4096;

}

table eg_set {
    reads {
        routing_metadata.o_lif : exact;
    }
    actions {
        set_egress_info;
    }
}

table eg_acl {
    reads {
        egress_metadata.o_acl_label : lpm;
        ipv4.dstAddr : lpm;
    }
    actions {
        eg_drop_packet;
        eg_pass;
    }
}
