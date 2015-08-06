# vim: set expandtab ts=4 sw=4:
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

import utils

from packet_base import packet_base
from ip_address import IpAddress

class ipv4(packet_base):
    IPv4 = 4
    ICMP_PROTOCOL = 1
    TCP_PROTOCOL  = 6
    UDP_PROTOCOL  = 17

    def __init__(self):
        self.srcip = IpAddress()
        self.dstip = IpAddress()
        self.protocol = 0
        self.tos = 0
        self.id = 0xDEADBEEF
        self.flags = 0
        self.frag = 0
        self.ttl = 64
        self.csum  = 0

    def __repr__(self):
        if self.next != None:
            payload = " <- " + repr(self.next)
        else:
            payload = ""
        return "ipv4: " + str((self.protocol, self.srcip, self.dstip)) + payload

    def copy(self):
        cpy = ipv4()
        cpy.srcip = self.srcip.copy()
        cpy.dstip = self.dstip.copy()
        cpy.protocol = self.protocol
        cpy.tos = self.tos
        cpy.id = self.id
        cpy.flags = self.flags
        cpy.frag = self.frag
        cpy.ttl = self.ttl
        cpy.csum  = self.csum
        if self.next != None:
            cpy.set_payload(self.next.copy())
        return cpy

    def dump_equivalent_state(self):
        filtered_dict = packet_base.dump_equivalent_state(self)
        filtered_dict["srcip"] = utils.copy_state(self.srcip)
        filtered_dict["dstip"] = utils.copy_state(self.dstip)
        filtered_dict["protocol"] = utils.copy_state(self.protocol)
        filtered_dict["tos"] = utils.copy_state(self.tos)
        filtered_dict["id"] = utils.copy_state(self.id)
        filtered_dict["flags"] = utils.copy_state(self.flags)
        filtered_dict["frag"] = utils.copy_state(self.frag)
        filtered_dict["ttl"] = utils.copy_state(self.ttl)
        filtered_dict["csum"] = utils.copy_state(self.csum)
        if next != None:
            filtered_dict["next"] = utils.copy_state(self.next)
        return filtered_dict

    def toScapy(self):
        from scapy.layers.inet import IP

        tos = self.tos
        id = self.id
        flags = self.flags
        frag = self.frag
        ttl = self.ttl
        proto = self.protocol
        chksum = None if self.csum == 0 else self.csum      # TODO: reconsider automatic chksum computation
        src = str(self.srcip)
        dst = str(self.dstip)
        # left are: version - default 4, ihl?, len, options

        p = IP(tos = tos, id = id, flags = flags, frag = frag, ttl = ttl, proto = proto, src = src, dst = dst)

        if self.next == None:
            return IP(str(p)), None
        elif isinstance(self.next, packet_base):
            p2, data = self.next.toScapy()
            return IP(str(p/p2)), data
        elif isinstance(self.next, str):
            return IP(str(p)), self.next


