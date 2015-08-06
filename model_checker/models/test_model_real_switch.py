#
# Copyright (c) 2011, EPFL (Ecole Politechnique Federale de Lausanne)
# All rights reserved.
#
# Created by Marco Canini, Daniele Venzano, Dejan Kostic, Jennifer Rexford
# Contributed to this file: Maciej Kuzniar
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

from real_switch.of_switch_real import OpenflowSwitchReal
from real_switch.virtual_switch import OpenFlowUserSwitch, OVSSwitch, HpSwitch
from clients.arrival import Arrival, IPArrival
from clients.replier import Replier 
from of_controller.nox_controller import Controller
from invariants.no_loop_invariant import NoLoopInvariant
from invariants.no_drop_mobile_invariant import NoDropMobileInvariant
from invariants.direct_route_invariant import DirectRouteInvariant
from invariants.strict_direct_route_invariant import StrictDirectRouteInvariant
from invariants.not_matching_switch_outputs import NotMatchingSwitchOutputs

import config_parser as config

class TestController(Controller):
    def __init__(self):
        from test.test_ctrl import testCtrl
        Controller.__init__(self, testCtrl)

    def process_packet(self):
        raise NotImplementedError

    def isSameMicroflow(self, packet1, packet2):
        return (packet1.src == packet2.src and packet1.dst == packet2.dst)

    def __repr__(self):
        return str(self.component)

class TestModelRealSwitch(Model):
    invariants = [NoLoopInvariant, DirectRouteInvariant, StrictDirectRouteInvariant, NoDropMobileInvariant, NotMatchingSwitchOutputs]

    def initTopology(self, topo):
        # Define the controller
        self.controller = TestController()
        # Define the switches
        sw1 = OpenflowSwitchReal(name="s1", port_count=2, of_id=1, expire_entries=config.get("model.flow_entry_expiration"))
        # Define the clients and thier addresses
        mac1 = (0x00, 0x00, 0x00, 0x00, 0x01, 0x00)
        mac2 = (0x00, 0x00, 0x00, 0x00, 0x01, 0x01)
        mac3 = (0x00, 0x00, 0x00, 0x01, 0x01, 0x01)
#       cl1 = Arrival(name="h1", mymac=mac1, dstmac=mac2, pkts=config.get("pyswitch_model.pkts"), sequential=config.get("pyswitch_model.sequential"))
#       cl2 = Arrival(name="h2", mymac=mac2, dstmac=mac1, pkts=config.get("pyswitch_model.pkts"), sequential=config.get("pyswitch_model.sequential"))
        ip1 = "128.0.0.11"
        ip2 = "128.0.0.12"
        ip3 = "128.0.0.13"
        cl1 = IPArrival(name="h1", mymac=mac1, myip=ip1, pkts=config.get("pyswitch_model.pkts"), sequential=config.get("pyswitch_model.sequential"))
        cl2 = IPArrival(name="h2", mymac=mac2, myip=ip2, pkts=config.get("pyswitch_model.pkts"), sequential=config.get("pyswitch_model.sequential"))

        # topology connections: sw1 port 0 is connected to port 0 of cl1, port 1 connected to port 0 of sw2
        sw1.initTopology({0: (cl1, 0), 1: (cl2, 0)})
        cl1.initTopology({0: (sw1, 0)})
        cl2.initTopology({0: (sw1, 1)})
        # Add clients and switches to the model list
        self.clients.append(cl1)
        self.clients.append(cl2)
        self.switches.append(sw1)
        self.switches_idx[sw1.getOpenflowID()] = sw1
        # start callbacks
        self.controller.start_callbacks.append(lambda: self.controller.install())
        self.controller.start_callbacks.append(lambda: self.controller.addSwitch(sw1))

        sw1.setRealSwitch(HpSwitch, "128.178.149.155", "eth0", {0 : 3, 1 : 4}, 0, ["eth1", "eth2"])
        sw1.setRealSwitch(OpenFlowUserSwitch, "127.0.0.1", "lo", {0 : 1, 1 : 2})
        sw1.setRealSwitch(OVSSwitch, "127.0.0.1", "lo", {0 : 1, 1 : 2})

    def start(self, model_checker):
        Model.start(self, model_checker)
        mac1 = (0x00, 0x00, 0x00, 0x00, 0x01, 0x00)
        mac2 = (0x00, 0x00, 0x00, 0x00, 0x01, 0x01)
        mac3 = (0x00, 0x00, 0x00, 0x01, 0x01, 0x01)
        ip1 = "128.0.0.11"
        ip2 = "128.0.0.12"
        ip3 = "128.0.0.13"
        self.clients[0].enableAction("send_packet", (mac1, ip1))
        self.clients[0].enableAction("send_packet", (mac2, ip2))
        self.clients[0].enableAction("send_packet", (mac3, ip3))

    def generate_inputs(self):
        pass

    def generate_stats(self):
        pass

