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

/* Should be 16 tables
 * Do we need check_ipv6_size though? it kinda sucks
 */
#define ROUTABLE_SIZE 64
#define SMAC_VLAN_SIZE 160000
#define VRF_SIZE 40000
#define CHECK_IPV6_SIZE 1
#define IPv6_PREFIX_SIZE 1000
#define CHECK_UCAST_IPV4_SIZE 1
#define IPV4_FORWARDING_SIZE 160000
#define IPV6_FORWARDING_SIZE 5000
#define NEXT_HOP_SIZE 41250
#define IPV4_XCAST_FORWARDING_SIZE 16000
#define IPV6_XCAST_FORWARDING_SIZE 1000
#define URPF_V4_SIZE 160000
#define URPF_V6_SIZE 5000
#define IGMP_SNOOPING_SIZE 16000
#define DMAC_VLAN_SIZE 160000
#define ACL_SIZE 80000

#define VRF_BIT_WIDTH 12
