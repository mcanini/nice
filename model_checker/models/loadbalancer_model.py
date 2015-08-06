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
from clients.tcp_client import TcpClient
from clients.tcp_server import TcpServer
from of_controller.nox_controller import LoadBalancerController
from invariants.one_flow_one_destination import OneTCPFlowOneDestination
from invariants.no_forgotten_packets_config import NoForgottenTcpPacketsAfterConfig
from invariants.no_forgotten_packets import NoForgottenTCPPacketsBuilder, NoForgottenARPPacketsBuilder
from invariants.no_drop_invariant import NoDropARPBuilder, NoDropTCPBuilder


import config_parser as config

class LoadBalancerModel(Model):
    invariants = [NoForgottenTcpPacketsAfterConfig, NoForgottenTCPPacketsBuilder, NoDropTCPBuilder, NoForgottenARPPacketsBuilder, NoDropARPBuilder, OneTCPFlowOneDestination]

    def initTopology(self, topo):
        self.controller = LoadBalancerController(use_fixed=config.get("loadbalancer_model.use_fixed_version"))
        r1 = TcpServer(name="replica1", mymac=(0, 0xee, 0xee, 0, 0, 1), myip=(20, 0, 0, 1))
        r2 = TcpServer(name="replica2", mymac=(0, 0xee, 0xee, 0, 0, 2), myip=(20, 0, 0, 2))
#       sw1 = OpenflowSwitch(name="s1", port_count=4, of_id=0x000102030401)
        sw1 = OpenflowSwitch(name="s1", port_count=3, of_id=0x000102030401, expire_entries=config.get("model.flow_entry_expiration"))
        cl1 = TcpClient(name="h1", mymac=(0, 0xcc, 0xcc, 0, 0, 0x01), myip=(1, 0, 0, 1),
                    pkts=config.get("loadbalancer_model.connections"), destip=(20,0,0,5))
#       cl2 = TcpClient(name="h2", mymac=(0, 0xcc, 0xcc, 0, 0, 0x02), myip=(128, 0, 0, 1), pkts=self.num_pkts_to_inject)

#       sw1.initTopology({0: (r1, 0), 1: (r2, 0), 2: (cl1, 0), 3: (cl2, 0)})
        sw1.initTopology({0: (r1, 0), 1: (r2, 0), 2: (cl1, 0)})
        cl1.initTopology({0: (sw1, 2)})
#       cl2.initTopology({0: (sw1, 3)})
        r1.initTopology({0: (sw1, 0)})
        r2.initTopology({0: (sw1, 1)})
        self.clients.append(cl1)
#       self.clients.append(cl2)
        self.clients.append(r1)
        self.clients.append(r2)
        self.switches.append(sw1)
        self.switches_idx[sw1.getOpenflowID()] = sw1
        # start callbacks
        self.controller.start_callbacks.append(lambda: self.controller.install())
        self.controller.start_callbacks.append(lambda: self.controller.addSwitch(sw1))

    def generate_inputs(self):
        pass

    def generate_stats(self):
        pass

