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

class StrictDirectRouteInvariant(Invariant):
    def __init__(self):
        Invariant.__init__(self, "StrictDirectRoute")

    def path_start_cb(self, model):
        self.exchanges = []

    def packet_sent_cb(self, model, sender, receiver, packet):
        key1 = self.exchangeKey(packet.src, packet.dst)
        key2 = self.exchangeKey(packet.dst, packet.src)
        if key1 in self.exchanges and key2 in self.exchanges:
            assert packet.annotation == []
            packet.annotation.append("STRICT_DIRECT")

    def packet_received_cb(self, model, receiver, packet, port):
        key2 = self.exchangeKey(packet.dst, packet.src)

        if key2 not in self.exchanges:
            self.exchanges.append(key2)

    def exchangeKey(self, srcaddr, dstaddr):
        key = str(srcaddr) + "->" + str(dstaddr)
        return key

    def before_cnt_packet_in_cb(self, model, buffer_id, packet, inport, reason, dp_id):
        if "STRICT_DIRECT" in packet.annotation:
            v = Violation(self, "Strict: Packet should have gone on a direct route!")
            self.reportViolation(v)
        return

    def dump_equivalent_state(self):
        filtered_dict = {}
        filtered_dict["exchanges"] = utils.copy_state(self.exchanges)
        return filtered_dict
