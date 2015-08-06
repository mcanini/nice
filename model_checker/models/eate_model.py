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

from lib.model import Model

from of_switch.of_switch import OpenflowSwitch
from clients.tcp_client import TcpClient
from clients.tcp_server import TcpServer
from of_controller.nox_controller import EateController

from invariants.eate_route_invariant import EateRouteInvariant
from invariants.no_forgotten_packets import NoForgottenTCPPacketsBuilder, NoForgottenARPPacketsBuilder
from invariants.no_drop_invariant import NoDropARPBuilder, NoDropTCPBuilder

import config_parser as config

class EateModel(Model):
    invariants = [NoForgottenTCPPacketsBuilder, NoDropTCPBuilder, NoForgottenARPPacketsBuilder, NoDropARPBuilder, EateRouteInvariant]
    generate_inputs = False
    generate_stats = True

    def initTopology(self, topo):
        self.controller = EateController(version=config.get("eate_model.app_version"))
        s_b = OpenflowSwitch(name="s_b", port_count=3+1, of_id=1, expire_entries=config.get("model.flow_entry_expiration"))
        s_c = OpenflowSwitch(name="s_c", port_count=4+1, of_id=2, expire_entries=config.get("model.flow_entry_expiration"))
        s_i = OpenflowSwitch(name="s_i", port_count=2+1, of_id=3, expire_entries=config.get("model.flow_entry_expiration"))
        h_b1_ip = (10, 0, 0, 11)
        h_x1_ip = (10, 0, 0, 13)
        h_y1_ip = (10, 0, 0, 14)
        h_b1_mac = (10, 0, 0, 0, 0, 0x0B) 
        h_x1_mac = (10, 0, 0, 0, 0, 0x0C)
        h_y1_mac = (10, 0, 0, 0, 0, 0x0D)
        h_b1 = TcpClient(name="h_b1", mymac=h_b1_mac, myip=h_b1_ip, destip=[h_x1_ip, h_y1_ip], pkts=config.get("eate_model.connections")) #, h1ip = h_x1_ip, h2ip=h_y1_ip)
        h_x1 = TcpServer(name="h_x1", mymac=h_x1_mac, myip=h_x1_ip)
        h_y1 = TcpServer(name="h_y1", mymac=h_y1_mac, myip=h_y1_ip)
        h_b1.initTopology({0: (s_b, 3)})
        h_x1.initTopology({0: (s_c, 3)})
        h_y1.initTopology({0: (s_c, 4)})
        s_b.initTopology({1: (s_i, 1), 2: (s_c, 1), 3: (h_b1, 0)})
        s_c.initTopology({1: (s_b, 2), 2: (s_i, 2), 3: (h_x1, 0), 4: (h_y1, 0)})
        s_i.initTopology({1: (s_b, 1), 2: (s_c, 2)})
        self.clients.append(h_b1)
        self.clients.append(h_x1)
        self.clients.append(h_y1)
        self.switches.append(s_b)
        self.switches.append(s_c)
        self.switches.append(s_i)
        self.switches_idx[s_b.getOpenflowID()] = s_b
        self.switches_idx[s_c.getOpenflowID()] = s_c
        self.switches_idx[s_i.getOpenflowID()] = s_i
        h_x1.controller = self.controller
        #start callbacks
        self.controller.start_callbacks.append(lambda: self.controller.install())
        self.controller.start_callbacks.append(lambda: self.controller.addSwitch(s_b))
        self.controller.start_callbacks.append(lambda: self.controller.addSwitch(s_c))
        self.controller.start_callbacks.append(lambda: self.controller.addSwitch(s_i))

    def addNewStats(self, dp_id, stats):
        self.controller.enableAction("port_stats", (dp_id, stats))
