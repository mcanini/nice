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

from lib.model import Model

from of_switch.of_switch import OpenflowSwitch
from clients.replier import Replier 
from clients.sym_exec_sender import SymExecSender
from of_controller.nox_controller import PySwitchController

from invariants.no_loop_invariant import NoLoopInvariant
from invariants.strict_direct_route_invariant import StrictDirectRouteInvariant

import config_parser as config

class NiceModel(Model):
    generate_inputs = True
    generate_stats = False
    invariants = [NoLoopInvariant, StrictDirectRouteInvariant]

    def initTopology(self, topo):
        self.controller = PySwitchController()
        sw1 = OpenflowSwitch(name="s1", port_count=2, of_id=1, expire_entries=config.get("model.flow_entry_expiration"))
        sw2 = OpenflowSwitch(name="s2", port_count=2, of_id=2, expire_entries=config.get("model.flow_entry_expiration"))
        cl1 = SymExecSender(name="h1", mymac=(0x00, 0xBA, 0xAD, 0xF0, 0x0D, 0x01), max_pkts=config.get("nice_model.max_pkts"), max_burst=config.get("nice_model.max_burst"))
        cl2 = Replier(name="h2", mymac=(0x00, 0x01, 0x02, 0x03, 0x04, 0x05))
        sw1.initTopology({0: (cl1, 0), 1: (sw2, 0)})
        sw2.initTopology({0: (sw1, 1), 1: (cl2, 0)})
        cl1.initTopology({0: (sw1, 0)})
        cl2.initTopology({0: (sw2, 1)})
        self.clients.append(cl1)
        self.clients.append(cl2)
        self.switches.append(sw1)
        self.switches.append(sw2)
        self.switches_idx[sw1.getOpenflowID()] = sw1
        self.switches_idx[sw2.getOpenflowID()] = sw2
        # start callbacks
        self.controller.start_callbacks.append(lambda: self.controller.install())
        self.controller.start_callbacks.append(lambda: self.controller.addSwitch(sw1))
        self.controller.start_callbacks.append(lambda: self.controller.addSwitch(sw2))

