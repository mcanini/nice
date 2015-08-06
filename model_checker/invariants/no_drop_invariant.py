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

from invariant import Invariant
from violation import Violation
import utils

from nox.lib.packet.mac_address import MacAddress

import logging
log = logging.getLogger("nice.mc.inv.nodrop")

class NoDropInvariant(Invariant):
    def __init__(self, packet_type=None):
        self.packet_store = {}
        self.packet_type = packet_type
        name = "NoDrop"
        if packet_type:
            name += " %s" % packet_type

        Invariant.__init__(self, name)

    def path_start_cb(self, model):
        self.packet_store = {}

    def packet_sent_cb(self, model, sender, receiver, packet):
        if packet.packet_id == None:
            utils.crash("packet with no packet_id: %s" % packet)
        if packet.packet_id in self.packet_store:
            utils.crash("sending packet with duplicate ID: %s" % packet)
        else:
            self.packet_store[packet.packet_id] = [packet, 1]
        log.debug("sent packet: %s, 1" % packet.name)

    def packet_received_cb(self, model, receiver, packet, port):
        if receiver.name == "ctrl":
            return
        if packet.dst != MacAddress("ff:ff:ff:ff:ff:ff") and receiver.mymac != packet.dst:
            return
        if packet.packet_id == None:
            utils.crash("packet with no packet_id: %s" % packet)
        if not packet.packet_id in self.packet_store:
            utils.crash("packet received but never sent: %s" % packet)

        if self.packet_store[packet.packet_id][1] > 0: # if there was flooding, packet may arrive more times than it was sent
            self.packet_store[packet.packet_id][1] -= 1
        log.debug("received packet: %s, %d" % (packet.name, self.packet_store[packet.packet_id][1]))

    def path_end_cb(self, model, cached_state):
        if cached_state:
            return
   
        if self.packet_type:
            dropped_packets = [p.name for (p, cnt) in self.packet_store.values() if cnt and p.find(self.packet_type) and [c for c in model.clients if c.mymac == p.dst]]
        else:
            dropped_packets = [p.name for (p, cnt) in self.packet_store.values() if cnt and [c for c in model.clients if c.mymac == p.dst]]

        if dropped_packets:
            s = ", ".join(dropped_packets)
#           s = "dropped packets:\n" + s
            v = Violation(self, "Dropped packets: %s" % s)
            self.reportViolation(v)

    def dump_equivalent_state(self):
        filtered_dict = {}
        filtered_dict["store"] = utils.copy_state(self.packet_store)
        filtered_dict["type"] = str(self.packet_type)
        return filtered_dict


def NoDropARPBuilder():
    return NoDropInvariant("arp")

def NoDropTCPBuilder():
    return NoDropInvariant("tcp")
