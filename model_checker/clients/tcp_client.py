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

from nox.lib.packet import arp, ethernet, ipv4, tcp
from nox.lib.packet.ip_address import IpAddress

class TcpClient(Host):
    TCP_NOT_CONNECTED = 0
    TCP_SYN_SENT = 1
    TCP_CONNECTED = 2
    ARP_WAIT = 3

    def __init__(self, name, mymac=(0,0,0,0,0,0), myip=(0,0,0,0), destip=(0,0,0,0), pkts=1):
        Host.__init__(self, name, mymac, myip)
        self.pkts_to_send = pkts
        self.pkts_sent = 0
        self.received_pkt_count = 0
        self.current_destip_idx = 0
        if isinstance(destip, list):
            self.destip = map(lambda x: IpAddress(x), destip)
        else:
            self.destip = [IpAddress(destip)]
        self.flows_started = 0
        self.connections = {}

    def start(self, model_checker):
        Host.start(self, model_checker)
        flow_id = self.flows_started
        self.flows_started += 1
        self.enableAction("start_connection", flow_id)

    def start_connection(self, flow_id):
        if not self.connections.has_key(flow_id):
            self.connections[flow_id] = self.TCP_NOT_CONNECTED

        destmac = self.ip2mac(self.destip[self.current_destip_idx])
        if destmac != None:
            self.start_tcp_connection(destmac, self.destip[self.current_destip_idx], 80, flow_id)
            self.connections[flow_id] = self.TCP_SYN_SENT
            if (self.flows_started < self.pkts_to_send):
                self.enableAction("start_connection", (self.flows_started))
                self.flows_started += 1
                self.current_destip_idx += 1
                self.current_destip_idx = self.current_destip_idx % len(self.destip)
        elif self.connections[flow_id] == self.TCP_NOT_CONNECTED: # We need to do an ARP query
            self.connections[flow_id] = self.ARP_WAIT

        return True

    def process_packet(self):
        self.received_pkt_count = self.received_pkt_count + 1
        packet = self.getWaitingPacket(0)
        if not packet.dst in [ethernet.ETHER_BROADCAST, ethernet.ETHER_ANY, self.mymac]:
            return not self.checkWaitingPacket(0)

        arp_pkt = packet.find('arp')
        if arp_pkt != None:
            self.manage_arp_packet(arp_pkt)
            if arp_pkt.opcode == arp.arp.REPLY:
                for flow_id in self.connections:
                    if self.connections[flow_id] == self.ARP_WAIT:
                        # possible optimization: should reeanable only the right ones
                        self.enableAction("start_connection", flow_id, skip_dup=True)

        ip_pkt = packet.find("ipv4")
        if ip_pkt != None and ip_pkt.dstip != self.myip: # FIXME IP broadcasts, multicast, etc...
            return not self.checkWaitingPacket(0)

        tcp_pkt = packet.find('tcp')
        if tcp_pkt != None:
            if self.connections[tcp_pkt.flow_id] == self.TCP_SYN_SENT:
                if tcp_pkt.flags & tcp_pkt.SYN and tcp_pkt.flags & tcp_pkt.ACK:
                    self.log.info("Concluding tcp handshake")
                    self.connections[tcp_pkt.flow_id] = self.TCP_CONNECTED
                    pkt = self.build_tcp_packet(tcp_pkt.dstport, tcp_pkt.srcport, tcp.tcp.ACK, tcp_pkt.flow_id, tcp_pkt.ack+1, tcp_pkt.seq+1)
                    pkt = self.build_ipv4_packet(ipv4.ipv4.TCP_PROTOCOL, packet.next.srcip, pkt)
                    pkt = self.build_ethernet_packet("tcpack", packet.src, pkt, ethernet.ethernet.IP_TYPE)
                    # send the packet, should try also using an action here
                    self.sendPacket(pkt, 0)

        return not self.checkWaitingPacket(0)

    def start_tcp_connection(self, destmac, destip, dest_tcpport, flow_id):
        self.log.info("Starting a new TCP connection")
        pkt = self.build_tcp_packet(80, dest_tcpport, tcp.tcp.SYN, flow_id, 0, 0)
        pkt = self.build_ipv4_packet(ipv4.ipv4.TCP_PROTOCOL, destip, pkt)
        pkt = self.build_ethernet_packet("tcpsyn", destmac, pkt, ethernet.ethernet.IP_TYPE)
        self.state.testPoint("tcp_connection_start", client=self, packet=pkt)
        # send the packet
        self.sendPacket(pkt, 0)

    def dump_equivalent_state(self):
        filtered_dict = Host.dump_equivalent_state(self)
        filtered_dict["received_pkt_count"] = utils.copy_state(self.received_pkt_count)
        filtered_dict["connections"] = utils.copy_state(self.connections)
        return filtered_dict

