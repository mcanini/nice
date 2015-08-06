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

from invariant import Invariant
from violation import Violation

import utils

class OneTCPFlowOneDestination(Invariant):
    def __init__(self):
        Invariant.__init__(self, "OneTCPFlowOneDestination")

    def path_start_cb(self, model):
        self.flows = {}

    def tcp_connection_start_cb(self, model, client, packet):
        tcp_pkt = packet.find("tcp")
        if tcp_pkt == None:
            return
        self.flows[tcp_pkt.flow_id] = (packet.src, None) # the destination is not yet known

    def syn_packet_received_cb(self, model, receiver, packet):
        tcp_pkt = packet.find("tcp")
        if tcp_pkt == None:
            return
        if not tcp_pkt.flow_id in self.flows:
            utils.crash("unknown flow")
        entry = self.flows[tcp_pkt.flow_id]
        if entry[0] != packet.src:
            v = Violation(self, "wrong source MAC address rewriting")
            self.reportViolation(v)
        entry = (entry[0], packet.dst)
        self.flows[tcp_pkt.flow_id] = entry

    def ack_packet_received_cb(self, model, receiver, packet):
        server_mac = receiver.mymac
        tcp_pkt = packet.find("tcp")
        if tcp_pkt == None:
            return
        if not tcp_pkt.flow_id in self.flows:
            utils.crash("unknown flow")
        entry = self.flows[tcp_pkt.flow_id]
        if entry[0] != packet.src:
            v = Violation(self, "wrong source MAC address rewriting")
            self.reportViolation(v)
        if entry[1] != server_mac:
            v = Violation(self, "packet matching one flow sent to another server")
            self.reportViolation(v)

    def dump_equivalent_state(self):
        filtered_dict = {}
        filtered_dict["flows"] = utils.copy_state(self.flows)
        return filtered_dict
