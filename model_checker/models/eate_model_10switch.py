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

# Double diamond topology:
#       7 - 8
#      /     \
# C - 2       10 - E
#      \     /
#       5 - 6
#      /     \
# B - 1       9 - D
#      \     /
#       3 - 4

from lib.model import Model

from of_switch.of_switch import OpenflowSwitch
from clients.tcp_client import TcpClient
from clients.tcp_server import TcpServer
from of_controller.nox_controller import EateController

#from invariants.eate_route_invariant import EateRouteInvariant
from invariants.no_drop_invariant import NoDropInvariant
from invariants.no_loop_invariant import NoLoopInvariant

import config_parser as config

class EateModel10Switch(Model):
#   invariants = [EateRouteInvariant]
    invariants = [NoDropInvariant, NoLoopInvariant]
    generate_inputs = False
    generate_stats = True

    def initTopology(self, topo):
        self.controller = EateController(version=config.get("eate_model.app_version"))
        s_1 = OpenflowSwitch(name="s_1", port_count=3+1, of_id=1, expire_entries=config.get("model.flow_entry_expiration"))
        s_2 = OpenflowSwitch(name="s_2", port_count=3+1, of_id=2, expire_entries=config.get("model.flow_entry_expiration"))
        s_3 = OpenflowSwitch(name="s_3", port_count=2+1, of_id=3, expire_entries=config.get("model.flow_entry_expiration"))
        s_4 = OpenflowSwitch(name="s_4", port_count=2+1, of_id=4, expire_entries=config.get("model.flow_entry_expiration"))
        s_5 = OpenflowSwitch(name="s_5", port_count=3+1, of_id=5, expire_entries=config.get("model.flow_entry_expiration"))
        s_6 = OpenflowSwitch(name="s_6", port_count=6+1, of_id=6, expire_entries=config.get("model.flow_entry_expiration"))
        s_7 = OpenflowSwitch(name="s_7", port_count=2+1, of_id=7, expire_entries=config.get("model.flow_entry_expiration"))
        s_8 = OpenflowSwitch(name="s_8", port_count=2+1, of_id=8, expire_entries=config.get("model.flow_entry_expiration"))
        s_9 = OpenflowSwitch(name="s_9", port_count=3+1, of_id=9, expire_entries=config.get("model.flow_entry_expiration"))
        s_10 = OpenflowSwitch(name="s_10", port_count=3+1, of_id=10, expire_entries=config.get("model.flow_entry_expiration"))
        hb_ip = (10, 0, 0, 11)
        hc_ip = (10, 0, 0, 12)
        hd_ip = (10, 0, 0, 13)
        he_ip = (10, 0, 0, 14)
        hb_mac = (10, 0, 0, 0, 0, 0x0B) 
        hc_mac = (10, 0, 0, 0, 0, 0x0C)
        hd_mac = (10, 0, 0, 0, 0, 0x0D)
        he_mac = (10, 0, 0, 0, 0, 0x0E)
        hb = TcpClient(name="B", mymac=hb_mac, myip=hb_ip, destip=[he_ip], pkts=self.config.get("eate_model.connections")) #, h1ip = h_x1_ip, h2ip=h_y1_ip)
        hc = TcpClient(name="C", mymac=hc_mac, myip=hc_ip, destip=[hd_ip], pkts=self.config.get("eate_model.connections"))
        hd = TcpServer(name="D", mymac=hd_mac, myip=hd_ip)
        he = TcpServer(name="E", mymac=he_mac, myip=he_ip)
        hb.initTopology({0: (s_1, 3)})
        hc.initTopology({0: (s_2, 3)})
        hd.initTopology({0: (s_9, 3)})
        he.initTopology({0: (s_10, 3)})
        s_1.initTopology({1: (s_5, 1), 2: (s_3, 1), 3: (hb, 0)})
        s_2.initTopology({1: (s_5, 2), 2: (s_7, 1), 3: (hc, 0)})
        s_3.initTopology({1: (s_1, 2), 2: (s_4, 1)})
        s_4.initTopology({1: (s_3, 2), 2: (s_9, 2)})
        s_5.initTopology({1: (s_1, 1), 2: (s_2, 1), 3: (s_6, 1)})
        s_6.initTopology({1: (s_5, 3), 2: (s_10, 1), 3: (s_9, 1)})
        s_7.initTopology({1: (s_2, 2), 2: (s_8, 1)})
        s_8.initTopology({1: (s_7, 2), 2: (s_10, 2)})
        s_9.initTopology({1: (s_6, 3), 2: (s_4, 2), 3: (hd, 0)})
        s_10.initTopology({1: (s_6, 2), 2: (s_8, 2), 3: (he, 0)})
#       s_1.setPortsCanFail([1,2])
#       s_2.setPortsCanFail([1,2])
#       s_3.setPortsCanFail([2])
#       s_4.setPortsCanFail([2])
#       s_5.setPortsCanFail([3])
#       s_6.setPortsCanFail([2,3])
#       s_7.setPortsCanFail([2])
#       s_8.setPortsCanFail([2])
        self.clients.append(hb)
        self.clients.append(hc)
        self.clients.append(hd)
        self.clients.append(he)
        self.switches.append(s_1)
        self.switches.append(s_2)
        self.switches.append(s_3)
        self.switches.append(s_4)
        self.switches.append(s_5)
        self.switches.append(s_6)
        self.switches.append(s_7)
        self.switches.append(s_8)
        self.switches.append(s_9)
        self.switches.append(s_10)
        self.switches_idx[s_1.getOpenflowID()] = s_1
        self.switches_idx[s_2.getOpenflowID()] = s_2
        self.switches_idx[s_3.getOpenflowID()] = s_3
        self.switches_idx[s_4.getOpenflowID()] = s_4
        self.switches_idx[s_5.getOpenflowID()] = s_5
        self.switches_idx[s_6.getOpenflowID()] = s_6
        self.switches_idx[s_7.getOpenflowID()] = s_7
        self.switches_idx[s_8.getOpenflowID()] = s_8
        self.switches_idx[s_9.getOpenflowID()] = s_9
        self.switches_idx[s_10.getOpenflowID()] = s_10
        # Switch failures
        self.setSwitchFailuresCount(2)
        hb.controller = self.controller
        hc.controller = self.controller
        hd.controller = self.controller
        he.controller = self.controller
        #start callbacks
        self.controller.start_callbacks.append(lambda: self.controller.install())
        self.controller.start_callbacks.append(lambda: self.controller.addSwitch(s_1))
        self.controller.start_callbacks.append(lambda: self.controller.addSwitch(s_2))
        self.controller.start_callbacks.append(lambda: self.controller.addSwitch(s_3))
        self.controller.start_callbacks.append(lambda: self.controller.addSwitch(s_4))
        self.controller.start_callbacks.append(lambda: self.controller.addSwitch(s_5))
        self.controller.start_callbacks.append(lambda: self.controller.addSwitch(s_6))
        self.controller.start_callbacks.append(lambda: self.controller.addSwitch(s_7))
        self.controller.start_callbacks.append(lambda: self.controller.addSwitch(s_8))
        self.controller.start_callbacks.append(lambda: self.controller.addSwitch(s_9))
        self.controller.start_callbacks.append(lambda: self.controller.addSwitch(s_10))

    def addNewStats(self, dp_id, stats):
        self.controller.enableAction("port_stats", (dp_id, stats))

