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

import utils

from host import Host

from nox.lib.packet.ethernet import ETHER_BROADCAST

class Replier(Host):
    def __init__(self, name, mymac):
        Host.__init__(self, name, mymac, "10.0.0.1")
        self.packet_id = 1 # uses odd numbers
        self.move_host = False
        self.move_host_switch = None

    def send_packet(self, packet_id, dst):
        packet = self.build_ethernet_packet("pkt_reply", dst, None, 0)
        self.sendPacket(packet, 0)
        return True

    def process_packet(self):
        """ Dequeues a packet from port and processes it """
        pkt = self.getWaitingPacket(0)

        if pkt.dst == self.mymac:
            self.enableAction("send_packet", (self.packet_id, pkt.src))
            self.packet_id += 1
            if self.move_host:
                self.move_host = False
                self.enableAction("move_host_")
        return not self.checkWaitingPacket(0)

    def move_host_(self):
        sw = self.move_host_switch[0]
        port_from = self.move_host_switch[1]
        port_to = self.move_host_switch[2]
        sw.movePeer(port_from, port_to)
        self.ports[0].peer_port = port_to
        self.state.testPoint("client_move", client=self)
        # allow switch to learn about my mobility:
        packet = self.build_ethernet_packet("replier.mobility_inform", ETHER_BROADCAST, None, 0)
        self.sendPacket(packet, 0)
        return True

    def dump_equivalent_state(self):
        filtered_dict = Host.dump_equivalent_state(self)
        filtered_dict["move_host"] = utils.copy_state(self.move_host)
        return filtered_dict

