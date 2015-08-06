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

from ip_address import IpAddress
from packet_base import packet_base

from ethernet import ETHER_ANY 

import utils

class arp(packet_base):
    HW_TYPE_ETHERNET = 1
    PROTO_TYPE_IP    = 0x0800

    # opcodes:
    REQUEST     = 1 # ARP
    REPLY       = 2 # ARP
    REV_REQUEST = 3 # RARP
    REV_REPLY   = 4 # RARP

    def __init__(self):
        self.hwtype = self.HW_TYPE_ETHERNET
        self.opcode = 0
        self.prototype  = arp.PROTO_TYPE_IP
        self.hwsrc = ETHER_ANY
        self.hwdst = ETHER_ANY
        self.protosrc = IpAddress()
        self.protodst = IpAddress()

    def __repr__(self):
        if self.next != None:
            payload = " <- " + repr(self.next)
        else:
            payload = ""

        if self.hwtype == self.HW_TYPE_ETHERNET:
            hwt = "HW_TYPE_ETHERNET"
        else:
            utils.crash("Unknown ARP hwtype: 0x%x" % self.hwtype)

        if self.opcode == self.REQUEST:
            opc = "REQUEST"
        elif self.opcode == self.REPLY:
            opc = "REPLY"
        elif self.opcode == self.REV_REQUEST:
            opc = "REV_REQUEST"
        elif self.opcode == self.REV_REPLY:
            opc = "REV_REPLY"
        else:
            utils.crash("ARP opcode %d not known" % self.opcode)

        return "arp: " + str((hwt, opc, self.hwsrc, self.hwdst, self.protosrc, self.protodst)) + payload

    def copy(self):
        cpy = arp()
        cpy.hwtype = self.hwtype
        cpy.opcode = self.opcode
        cpy.prototype = self.prototype
        cpy.hwsrc = self.hwsrc.copy()
        cpy.hwdst = self.hwdst.copy()
        cpy.protosrc = self.protosrc.copy()
        cpy.protodst = self.protodst.copy()
        if self.next != None:
            self.set_payload(self.next.copy())
        return cpy

    def toScapy(self):
        from scapy.layers.l2 import ARP

        hwtype = self.hwtype
        ptype = self.prototype
        op = self.opcode
        hwsrc = str(self.hwsrc)
        hwdst = str(self.hwdst)
        psrc = str(self.protosrc)
        pdst = str(self.protodst)

        p = ARP(hwtype = hwtype, ptype = ptype, op = op, hwsrc = hwsrc, hwdst = hwdst, psrc = psrc, pdst = pdst)

        if self.next == None:
            return ARP(str(p)), None
        elif isinstance(self.next, packet_base):
            p2, data = self.next.toScapy()
            return ARP(str(p/p2)), data
        elif isinstance(self.next, str):
            return ARP(str(p)), self.next

    def dump_equivalent_state(self):
        filtered_dict = packet_base.dump_equivalent_state(self)
        filtered_dict["hwtype"] = utils.copy_state(self.hwtype)
        filtered_dict["opcode"] = utils.copy_state(self.opcode)
        filtered_dict["prototype"] = utils.copy_state(self.prototype)
        filtered_dict["hwsrc"] = utils.copy_state(self.hwsrc)
        filtered_dict["hwdst"] = utils.copy_state(self.hwdst)
        filtered_dict["protosrc"] = utils.copy_state(self.protosrc)
        filtered_dict["protodst"] = utils.copy_state(self.protodst)

