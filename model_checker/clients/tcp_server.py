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

from host import Host

from nox.lib.packet import ethernet, ipv4

class TcpServer(Host):
    TCP_NOT_CONNECTED = 0
    TCP_SYNACK_SENT = 1
    TCP_CONNECTED = 2

    def __init__(self, name, mymac, myip, tcp_port=80):
        Host.__init__(self, name, mymac, myip)
        self.received_pkt_count = 0
        self.myport = tcp_port
        self.controller = None
        self.connections = {}

    def start(self, model_checker):
        Host.start(self, model_checker)

    def process_packet(self):
        self.received_pkt_count = self.received_pkt_count + 1
        pkt = self.getWaitingPacket(0)
        if not pkt.dst in [ethernet.ETHER_BROADCAST, ethernet.ETHER_ANY, self.mymac]:
            # for the symbolic stats to kick in
            if self.controller:
                self.controller.packetLeftNetworkHandler()
            return not self.checkWaitingPacket(0)

        arp_pkt = pkt.find('arp')
        if arp_pkt != None:
            self.manage_arp_packet(arp_pkt)

        ip_pkt = pkt.find('ipv4')
        if ip_pkt != None and ip_pkt.dstip != self.myip:
            # for the symbolic stats to kick in
            if self.controller:
                self.controller.packetLeftNetworkHandler()
            return not self.checkWaitingPacket(0)

        tcp_pkt = pkt.find('tcp')
        if tcp_pkt != None and tcp_pkt.dstport == self.myport:
            self.manage_tcp_packet(pkt, tcp_pkt)

        # for the symbolic stats to kick in
        if self.controller:
            self.controller.packetLeftNetworkHandler()
        return not self.checkWaitingPacket(0)

    def manage_tcp_packet(self, pkt, tcp_pkt): # used only by the server
        if tcp_pkt.flags & tcp_pkt.SYN:
            self.log.info("SYN packet received")
            self.state.testPoint("syn_packet_received", receiver=self, packet=pkt)
            reply = self.build_tcp_packet(tcp_pkt.dstport, tcp_pkt.srcport, tcp_pkt.SYN | tcp_pkt.ACK, tcp_pkt.flow_id, 42, tcp_pkt.seq+1)
            reply = self.build_ipv4_packet(ipv4.ipv4.TCP_PROTOCOL, tcp_pkt.prev.srcip, reply)
            reply = self.build_ethernet_packet("tcpsynack", pkt.src, reply, ethernet.ethernet.IP_TYPE)
            # send the packet, try using an action here
            self.sendPacket(reply, 0)
            self.connections[tcp_pkt.flow_id] = self.TCP_SYNACK_SENT # TODO should add an invariant check to see if we were not already connected before (es. duplicate SYN)
        elif tcp_pkt.flags & tcp_pkt.ACK:
            self.log.info("ACK packet received")
            self.state.testPoint("ack_packet_received", receiver=self, packet=pkt)
            self.connections[tcp_pkt.flow_id] = self.TCP_CONNECTED # same as TCP_SYNACK_SENT
        else:
            self.log.error("Ignoring packet with unknown flags")

    def dump_equivalent_state(self):
        filtered_dict = Host.dump_equivalent_state(self)
        filtered_dict["received_pkt_count"] = utils.copy_state(self.received_pkt_count)
        return filtered_dict

