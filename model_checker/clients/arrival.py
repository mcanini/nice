#
# Copyright (c) 2011, EPFL (Ecole Politechnique Federale de Lausanne)
# All rights reserved.
#
# Created by Marco Canini, Daniele Venzano, Dejan Kostic, Jennifer Rexford
# Contributed to this file: Peter Peresini
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

from host import Host
from nox.lib.packet.mac_address import MacAddress
from nox.lib.packet.ip_address import IpAddress
from nox.lib.packet import ethernet, ipv4, tcp

import utils

class Arrival(Host):
    def __init__(self, name, mymac=(0,0,0,0,0,0), dstmac=(0,0,0,0,0,0), pkts=1, sequential=False):
        Host.__init__(self, name, mymac, "10.0.0.1")
        self.dstmac = MacAddress(dstmac)
        self.pkts = pkts
        self.received_pkt_count = 0
        self.sequential_packet_id = 1
        self.sequential = sequential

    def start(self, model_checker):
        Host.start(self, model_checker)
        self.enableAction("send_packet", (1))

    def send_packet(self, packet_id):
        packet = self.build_ethernet_packet("pkt%d" % packet_id, self.dstmac, None, 0)
        self.sendPacket(packet, 0)
        if not self.sequential:
            if (packet_id < self.pkts):
                self.enableAction("send_packet", (packet_id + 1))
        return True

    def process_packet(self):
        self.received_pkt_count = self.received_pkt_count + 1
        _pkt = self.getWaitingPacket(0)
        if self.sequential and (self.sequential_packet_id < self.pkts):
            self.sequential_packet_id += 1
            self.enableAction("send_packet", (self.sequential_packet_id))
        return not self.checkWaitingPacket(0)

    def dump_equivalent_state(self):
        filtered_dict = Host.dump_equivalent_state(self)
        filtered_dict["received_pkt_count"] = utils.copy_state(self.received_pkt_count)
        return filtered_dict


class IPArrival(Host):
    def __init__(self, name, mymac=(0,0,0,0,0,0), myip=(0,0,0,0), pkts=1, sequential=False):
        Host.__init__(self, name, mymac, myip)
        self.pkts = pkts
        self.received_pkt_count = 0
        self.sequential_packet_id = 1
        self.sequential = sequential

    def start(self, model_checker):
        Host.start(self, model_checker)

    def send_packet(self, dst_mac, dst_ip):
        flow_id = 1
        dest_tcpport = 20
        pkt = self.build_tcp_packet(80, dest_tcpport, tcp.tcp.SYN, flow_id, 0, 0)
        pkt = self.build_ipv4_packet(ipv4.ipv4.TCP_PROTOCOL, IpAddress(dst_ip), pkt)
        pkt = self.build_ethernet_packet("tcpsyn", MacAddress(dst_mac), pkt, ethernet.ethernet.IP_TYPE)
        self.sendPacket(pkt, 0)
        return True

    def process_packet(self):
        self.received_pkt_count = self.received_pkt_count + 1
        _pkt = self.getWaitingPacket(0)
        if self.sequential and (self.sequential_packet_id < self.pkts):
            self.sequential_packet_id += 1
            self.enableAction("send_packet", (self.sequential_packet_id))
        return not self.checkWaitingPacket(0)

    def dump_equivalent_state(self):
        filtered_dict = Host.dump_equivalent_state(self)
        filtered_dict["received_pkt_count"] = utils.copy_state(self.received_pkt_count)
        return filtered_dict

