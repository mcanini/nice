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
log = logging.getLogger("nice.mc.inv.nodropmobile")

# version of the invariant for mobile host
class NoDropMobileInvariant(Invariant):
    def __init__(self):
        Invariant.__init__(self, "NoDropMobile")

    def path_start_cb(self, model):
        self.packet_store = {}
        self.in_move = False

    def client_move_cb(self, model, client):
        self.in_move = True
        # clear all the packets in the move, they are allowed to be lost
        self.packet_store = {}

    def packet_sent_cb(self, model, sender, receiver, packet):
        log.debug("sent packet: %s" % packet)
        if packet.packet_id == None:
            utils.crash("packet with no packet_id: %s" % packet)
        if packet.packet_id in self.packet_store:
            utils.crash("sending packet with duplicate ID: %s" % packet)
        else:
            if not self.in_move:
                self.packet_store[packet.packet_id] = [packet, 1]

    def packet_received_cb(self, model, receiver, packet, port):
        log.debug("received packet: %s" % packet)
        if packet.name == "replier.mobility_inform":
            # information about move is distributed from this point
            # in time
            self.in_move = False

        if packet.packet_id == None:
            utils.crash("packet with no packet_id: %s" % packet)
        if not packet.packet_id in self.packet_store:
            # we are not tracking this packet
            return
        if packet.dst != MacAddress("ff:ff:ff:ff:ff:ff") and receiver.mymac != packet.dst:
            return

        if self.packet_store[packet.packet_id][1] > 0: # if there was flooding, a packet may arrive more times than it was sent
            self.packet_store[packet.packet_id][1] -= 1

    def path_end_cb(self, model, cached_state):
        if cached_state:
            return

        s = ", ".join(p[0].name for p in self.packet_store.values() if p[1] and [c for c in model.clients if c.mymac == p[0].dst])

        if s:
#           s = "dropped packets:\n" + s
            s = "dropped packets"
            v = Violation(self, s)
            self.reportViolation(v)
        if self.in_move:
            v = Violation(self, "A host is still moving")
            self.reportViolation(v)

    def dump_equivalent_state(self):
        filtered_dict = {}
        filtered_dict["in_move"] = utils.copy_state(self.in_move)
        filtered_dict["store"] = utils.copy_state(self.packet_store)
        return filtered_dict

