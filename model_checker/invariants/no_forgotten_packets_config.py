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

import logging
log = logging.getLogger("nice.mc.inv.noforgottenconfig")

class NoForgottenTcpPacketsAfterConfig(Invariant):
    def __init__(self):
        Invariant.__init__(self, "NoForgottenTcpPacketsAfterConfig")

    def path_start_cb(self, model):
        self.reconfig_happened = False
        self.packet_counts = {}
        for s in model.switches:
            self.packet_counts[s.name] = 0

    def reload_config_cb(self, model):
        self.reconfig_happened = True
        for s in model.switches:
            self.packet_counts[s.name] = self.count_tcp_packets(s)

    def path_end_cb(self, model, cached_state):
        if not self.reconfig_happened or cached_state:
            return

        new_counts = {}
        for s in model.switches:
            new_counts[s.name] = self.count_tcp_packets(s)

        for swname in new_counts:
            if new_counts[swname] > self.packet_counts[swname]:
                s = "%d TCP packets were forgotten in %s buffer" % (new_counts[swname] - self.packet_counts[swname], swname)
                v = Violation(self, s)
                self.reportViolation(v)

    def count_tcp_packets(self, switch):
        count = 0
        if len(switch.packet_store) > 0:
            for (p, port) in switch.packet_store.values():
                if p.find("tcp") != None:
                    count += 1
        return count

    def dump_equivalent_state(self):
        filtered_dict = {}
        filtered_dict["counts"] = utils.copy_state(self.packet_counts)
        return filtered_dict
