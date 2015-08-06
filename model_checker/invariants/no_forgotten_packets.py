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

import logging
log = logging.getLogger("nice.mc.inv.noforgotten")

class NoForgottenPackets(Invariant):
    def __init__(self, packet_type=None):
        self.packet_type = packet_type
        name = "NoForgottenPackets"
        if packet_type is not None:
            name += " %s" % packet_type

        Invariant.__init__(self, name)

    def path_end_cb(self, model, cached_state):
        if cached_state:
            return
        s = ""
        for sw in model.switches:
            if self.packet_type:
                forgotten_packets = [p for (p, port) in sw.packet_store.values() if p.find(self.packet_type)]
            else:
                forgotten_packets = sw.packet_store
            if forgotten_packets:
                s = "Packets forgotten in a buffer of switch %s" % (sw)
                v = Violation(self, s)
                self.reportViolation(v)


def NoForgottenARPPacketsBuilder():
    return NoForgottenPackets("arp")

def NoForgottenTCPPacketsBuilder():
    return NoForgottenPackets("tcp")
