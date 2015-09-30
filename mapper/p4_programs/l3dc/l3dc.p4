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

#include "parser.p4"
#include "headers.p4"
#include "actions.p4"
#include "tables.p4"

/* [USAGE NOTE]                                             */
/* This P4 file implements an L3-only MSDC spine device.    */

control ingress {
    apply(port);
    apply(src_mac);
    apply(router_mac);
    apply(host_route);
    apply(lpm_route);
    if ((routing_metadata.host_route_miss == 0) and
        (routing_metadata.lpm_route_miss == 0)) {
        apply(generate_hash); /* TODO: replace this with a "selector" */
        apply(ecmp_select);
        apply(lif);
        apply(lag_select);
    }
    apply(acl);
}

control egress {
    apply(eg_set);
    apply(eg_acl);
}

