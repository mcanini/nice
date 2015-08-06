#
# Copyright (c) 2011, EPFL (Ecole Politechnique Federale de Lausanne)
# All rights reserved.
#
# Created by Marco Canini, Daniele Venzano, Dejan Kostic, Jennifer Rexford
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   -  Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#   -  Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#   -  Neither the names of the contributors, nor their associated universities or
#      organizations may be used to endorse or promote products derived from this
#      software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
# SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

from mac_address import MacAddress
from ip_address import IpAddress

_ethtype_to_str = {}
_ipproto_to_str = {}

# Map ethernet oui to name
_ethoui2name = {}

# Map ethernet type to string
_ethtype_to_str[0x0800] = 'IP'
_ethtype_to_str[0x0806] = 'ARP'
_ethtype_to_str[0x8035] = 'RARP'
_ethtype_to_str[0x8100] = 'VLAN'
_ethtype_to_str[0x88cc] = 'LLDP'

# IP protocol to string
_ipproto_to_str[0]  = 'IP'
_ipproto_to_str[1]  = 'ICMP'
_ipproto_to_str[2]  = 'IGMP'
_ipproto_to_str[4]  = 'IPIP'
_ipproto_to_str[6]  = 'TCP'
_ipproto_to_str[9]  = 'IGRP'
_ipproto_to_str[17] = 'UDP'
_ipproto_to_str[47] = 'GRE'
_ipproto_to_str[89] = 'OSPF'

def mac_to_int(mac):
    value = 0
    for byte in mac:
        value = ((value << 8) | byte)
    return long(value)

def mac_to_str(a, _resolve_name=False):
    """ In pyswitch it is used only for logging """
    return repr(a)

def ip_to_str(a):
    return repr(a)
#    return "%d.%d.%d.%d" % ((a >> 24) & 0xff, (a >> 16) & 0xff, \
#                            (a >> 8) & 0xff, a & 0xff)

def ipstr_to_int(a):
    octets = a.split('.')
    octets = map(lambda x: int(x), octets)
    return IpAddress(tuple(octets))
#    return int(octets[0]) << 24 |\
#           int(octets[1]) << 16 |\
#           int(octets[2]) <<  8 |\
#           int(octets[3]);

def octstr_to_array(ocstr):
    a = []
    for item in ocstr.split(':'):
        a.append(int(item, 16))
    return MacAddress(tuple(a))

def ethtype_to_str(t):
    if t < 0x0600:
        return "llc"
    if _ethtype_to_str.has_key(t):
        return _ethtype_to_str[t]
    else:    
        return "%x" % t

def ipproto_to_str(t):
    if _ipproto_to_str.has_key(t):
        return _ipproto_to_str[t]
    else:    
        return "%x" % t

