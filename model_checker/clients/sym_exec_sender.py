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

from nox.lib.packet.mac_address import MacAddress
from nox.lib.packet import ethernet
from host import Host
import utils

import cPickle

class SymExecSender(Host):
    def __init__(self, name, mymac, filter_src_mac=True, max_pkts=1, max_burst=1):
        Host.__init__(self, name, mymac, "10.0.0.1")
        self.pkts = {}
        self.input_counter = 0
        self.filter_src_mac = filter_src_mac
        self.pkts_to_send = max_burst
        self.total_pkts = max_pkts
        self.sent_pkts = 0
        self.disabled_actions = []
        self.sym_exec_states = set()

    def start(self, model_checker):
        Host.start(self, model_checker)
        self.enableAction("discover_packets", skip_dup=True)

    def send_packet(self, packet_name):
        packet = self.pkts[str(packet_name)]
        packet.packet_id = self.genPacketID()
        self.sendPacket(packet, 0)
        
        self.sent_pkts += 1
        if self.sent_pkts == self.total_pkts:
            self.enabled_actions[:] = []
            return False
        self.pkts_to_send -= 1
        if self.pkts_to_send == 0:
            for act in self.enabled_actions:
                if act.target == "send_packet" and act.args[0] != packet_name:
                    self.disabled_actions.append(act)
            self.enabled_actions[:] = []
            return False
        return True

    def process_packet(self):
        if self.sent_pkts < self.total_pkts and self.pkts_to_send == 0:
            self.enabled_actions += self.disabled_actions
            self.disabled_actions = []
        self.pkts_to_send += 1
        _pkt = self.getWaitingPacket(0)
        return not self.checkWaitingPacket(0)

    def discover_packets(self):
        # sw_id = self.getPeer(0).openflow_id
        # inport = self.getPeerPort(0)
        ctrl_state = self.state.model.getControllerAppState()

        # dummy packet to feed to the symbolic engine as concolic input
        #FIXME useless code?
        packet = {}
        packet["name"] = "dummy.packet"
        packet["src"] = self.mymac.data
        packet["dst"] = (0, 0, 0, 0, 0, 0)
        packet["type"] = 0

        self.log.info("Calling SE to explore new state")

        symExecRPC = cPickle.dumps((packet, ctrl_state), 0)
        new_inputs = self.model_checker.generateInputs(symExecRPC)
        if new_inputs is not None:
            self.add_inputs(new_inputs)
    
        return True

    def add_inputs(self, inputs):
        aux = []
        count_good = 0
        count_bad = 0
        if isinstance(inputs, type({})):
            aux = [inputs["packet"]]
        elif isinstance(inputs, type([])):
            aux = map(lambda x: x["packet"], inputs)
        else:
            utils.crash("Unknown inputs provided: %s" % inputs)
        inputs = aux
        for p in inputs:
            if self.filter_src_mac: # sanity checks on the input packets
                macs = self.state.model.getClientMacAddresses()
                if p["src"] not in macs or p["dst"] not in macs or p["src"] != self.mymac or p["src"] == p["dst"]:
                    count_bad += 1
                    continue
            ep = ethernet.ethernet("se.packet%d" % self.input_counter)
            ep.src = MacAddress(p["src"])
            ep.dst = MacAddress(p["dst"])
            ep.parsed = p["parsed"]
            ep.next = p["next"]
            ep.type = p["type"]
            ep.arr = p["arr"]
            self.input_counter += 1
            count_good += 1
            self.pkts[ep.name] = ep
            self.enableAction("send_packet", ep.name)
        self.log.info("Accepted %d new packets, discarded %d invalid packets" % (count_good, count_bad))

    def enableDiscoveryIfNeeded(self, cur_state):
        ctrl_state = cur_state.model.getControllerAppState()
        ser_ctrl_state = cPickle.dumps(ctrl_state, -1)
        if not ser_ctrl_state in self.sym_exec_states and self.sent_pkts < self.total_pkts:
            self.enableAction("discover_packets", skip_dup=True)
            self.sym_exec_states.add(ser_ctrl_state)

    def dump_equivalent_state(self):
        filtered_dict = Host.dump_equivalent_state(self)
        filtered_dict["sent_packets"] = utils.copy_state(self.sent_pkts)
        filtered_dict["input_counter"] = utils.copy_state(self.input_counter)
        return filtered_dict
