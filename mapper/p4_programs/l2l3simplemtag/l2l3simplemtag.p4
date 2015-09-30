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

#include "defines.p4"
#include "parser.p4"
#include "headers.p4"
#include "actions.p4"
#include "tables.p4"

/* mTag information: http://www.sigcomm.org/sites/default/files/ccr/papers/2014/July/0000000-0000004.pdf */

control process_ip {
    apply(check_ipv6) {
        on_hit {
            apply(ipv6_prefix) {
                set_ipv6_prefix_ucast {
                    apply(urpf_v6);
                    apply(ipv6_forwarding);
                }
                set_ipv6_prefix_xcast {
                    apply(ipv6_xcast_forwarding);
                }
            }
        }
        on_miss {
            apply(check_ucast_ipv4) {
                on_hit {
                    apply(urpf_v4);
                    apply(ipv4_forwarding);
                }
                on_miss {
                    apply(igmp_snooping);
                    apply(ipv4_xcast_forwarding);
                }
            }
        }
    }
    apply(acl); /* Perhaps right before routable */
    apply(next_hop);
}

control process_mtag {
    apply(source_check);
    apply(dmac_vlan) {
        on_miss {
            apply(mtag_table);
        }
    }
    apply(eg_mtag_check);
}

control ingress {
    apply(smac_vlan);
    apply(vrf);
    apply(routable) {
        on_hit {
            process_ip();
            apply(dmac_vlan);
        }
        on_miss { /* check mTag */
            process_mtag();
        }
    }
}

control egress {
}
