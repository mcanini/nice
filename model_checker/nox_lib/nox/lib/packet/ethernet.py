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

import cPickle

from nox.lib.packet.mac_address import MacAddress
from nox.lib.packet.packet_base import packet_base

import utils

ETHER_ANY            = MacAddress((0, 0, 0, 0, 0, 0))
ETHER_BROADCAST      = MacAddress((0xff, 0xff, 0xff, 0xff, 0xff, 0xff))
BRIDGE_GROUP_ADDRESS = MacAddress((0x01, 0x80, 0xC2, 0x00, 0x00, 0x00))
LLDP_MULTICAST       = MacAddress((0x01, 0x80, 0xc2, 0x00, 0x00, 0x0e))
PAE_MULTICAST        = MacAddress((0x01, 0x80, 0xc2, 0x00, 0x00, 0x03)) # 802.1x Port Access Entity
NDP_MULTICAST        = MacAddress((0x01, 0x23, 0x20, 0x00, 0x00, 0x01)) # Nicira discovery multicast

class ethernet(packet_base):
    # Ethernet types
    ETH_TYPE = 1535 # (0x05ff)
    IP_TYPE = 2048
    ARP_TYPE = 2054
    RARP_TYPE = 32821
    VLAN_TYPE = 33024
    LLDP_TYPE = 35020
    PAE_TYPE = 34958

    def __init__(self, name="noname"):
        """ name is the name of ethernet packet """
        self.name = name
        self.src = MacAddress()
        self.dst = MacAddress()
        self.type = ethernet.ETH_TYPE
        self.arr = None
        self.packet_id = None # used by invariants
        self.annotation = [] # used by invariants
        self.fault_injection = [] # just for debugging, to help tracking packets around

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        if self.next != None:
            payload = " <- " + repr(self.next)
        else:
            payload = ""
        return "eth: " + str((self.name, self.packet_id, self.src, self.dst, self.type, self.fault_injection)) + payload

    def __ne__(self, other):
        if not isinstance(other, ethernet):
            return True
        else:
            return not(self.parsed == other.parsed and self.src == other.src and self.dst == other.dst and self.type == other.type and self.arr == other.arr and self.next == other.next)

    def __eq__(self, other):
        if not isinstance(other, ethernet):
            return False
        else:
            return self.parsed == other.parsed and self.src == other.src and self.dst == other.dst and self.type == other.type and self.arr == other.arr and self.next == other.next

    def __lt__(self, other):
        return self.name < other.name

    def __hash__(self):
        raise NotImplementedError
        ser = cPickle.dumps(self)
        return hash(ser)

    def dump_equivalent_state(self):
        filtered_dict = {}
        filtered_dict["name"] = utils.copy_state(self.name)
        filtered_dict["annotation"] = utils.copy_state(self.annotation)
#        filtered_dict["packet_id"] = None
#        filtered_dict["fault_injection"] = False
        filtered_dict["src"] = utils.copy_state(self.src)
        filtered_dict["dst"] = utils.copy_state(self.dst)
        filtered_dict["type"] = utils.copy_state(self.type)
        if self.next != None:
            filtered_dict["next"] = utils.copy_state(self.next)
        return filtered_dict

    def tostring(self):
        return self

    def copy(self):
        cpy = ethernet()
        cpy.name = self.name
        cpy.type = self.type
        cpy.arr = self.arr
        cpy.src = self.src.copy()
        cpy.dst = self.dst.copy()
        cpy.packet_id = self.packet_id
        cpy.annotation = list(self.annotation)
        cpy.fault_injection = self.fault_injection[:]
        if self.next != None:
            cpy.set_payload(self.next.copy())
        return cpy

    def toScapy(self):
        from scapy.layers.l2 import Ether
        from scapy.packet import Padding

        src = str(self.src)
        dst = str(self.dst)
        ptype = self.type
        name = self.name
        pid = self.packet_id
        #TODO: annotations?

        #mydata = struct.pack('!%ds%ds' % (len(self.packet_id), len(self.name)), self.packet_id, self.name)
        mydata = str(self.packet_id) + str(self.name)
        p = Ether(src = src, dst = dst, type = ptype)

        if self.next is None:
            return p, mydata
        elif isinstance(self.next, packet_base):
            p2, data = self.next.toScapy()
            if data is not None:
                mydata = mydata + data
            return p/p2, Padding(mydata)
        elif isinstance(self.next, str):
            return p, mydata + self.next
        



