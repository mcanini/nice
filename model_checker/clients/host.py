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

import abc

from lib.node import Node

from nox.lib.packet.mac_address import MacAddress
from nox.lib.packet.ip_address import IpAddress

from nox.lib.packet import ethernet, arp, tcp, ipv4
ARP_TYPE = ethernet.ethernet.ARP_TYPE

import utils

class Host(Node):
    def __init__(self, name, mymac, myip):
        Node.__init__(self, name, 1)
        self.mymac = MacAddress(mymac)
        self.myip = IpAddress(myip)
        self.arp_table = {}

    def start(self, model_checker):
        Node.start(self, model_checker)

    def build_ethernet_packet(self, name, dst, payload, type):
        eth = ethernet.ethernet(name)
        eth.packet_id = self.genPacketID()
        eth.set_payload(payload)
        if type != 0:
            eth.type = type
        eth.src = self.mymac.copy()
        eth.dst = dst.copy()
        return eth

    def build_ipv4_packet(self, protocol, dst, payload):
        ippkt = ipv4.ipv4()
        ippkt.protocol = protocol
        ippkt.srcip = self.myip.copy()
        ippkt.dstip = dst.copy()
        ippkt.set_payload(payload)
        return ippkt

    def build_arp_packet(self, opcode, hwdst, protodst):
        arppkt = arp.arp()
        arppkt.protosrc = self.myip.copy()
        arppkt.protodst = protodst.copy()
        arppkt.hwsrc = self.mymac.copy()
        arppkt.opcode = opcode
        return arppkt

    def build_tcp_packet(self, srcport, dstport, flags, flow_id, seq, ack):
        pkt = tcp.tcp()
        pkt.srcport = srcport
        pkt.dstport = dstport
        pkt.flags = flags
        pkt.seq = seq
        pkt.ack = ack
        pkt.flow_id = flow_id
        return pkt

    def manage_arp_packet(self, arp_pkt):
        """ RFC 826 without support for different protocol types """
#       import pdb; pdb.set_trace()
        if arp_pkt.prototype != arp.arp.PROTO_TYPE_IP:
            return
        merge_flag = False
        if self.arp_table.has_key(arp_pkt.hwsrc):
            self.log.debug("Adding %s to ARP table" % str((arp_pkt.hwsrc, arp_pkt.protosrc)))
            self.arp_table[arp_pkt.hwsrc] = arp_pkt.protosrc
            merge_flag = True
        if self.myip == arp_pkt.protodst:
            if not merge_flag:
                self.log.debug("Adding %s to ARP table" % str((arp_pkt.hwsrc, arp_pkt.protosrc)))
                self.arp_table[arp_pkt.hwsrc] = arp_pkt.protosrc
            if arp_pkt.opcode == arp.arp.REQUEST:
                reply = self.build_arp_packet(arp.arp.REPLY, arp_pkt.hwsrc, arp_pkt.protosrc)
                reply = self.build_ethernet_packet("arp_reply", arp_pkt.hwsrc, reply, ARP_TYPE)
                self.sendPacket(reply, 0)

    def arp_query(self, ip):
        name = "arp_query" + str(ip)
        packet = self.build_arp_packet(arp.arp.REQUEST, MacAddress("0:0:0:0:0:0"), ip)
        packet = self.build_ethernet_packet(name, ethernet.ETHER_BROADCAST, packet, ARP_TYPE)
        self.sendPacket(packet, 0)
        return True

    def ip2mac(self, ip):
        destmac = None
        for mac in self.arp_table:
            if self.arp_table[mac] == ip:
                destmac = mac
                break
        if destmac != None:
            return destmac
        else: # We need to do an ARP query
            self.log.info("Issuing ARP Request for %s" % ip)
            self.arp_query(ip)
            return None

    def process_packet(self):
        raise NotImplementedError

    @abc.abstractmethod
    def dump_equivalent_state(self):
        filtered_dict = Node.dump_equivalent_state(self)
        filtered_dict["arp_table"] = utils.copy_state(self.arp_table)
        return filtered_dict

