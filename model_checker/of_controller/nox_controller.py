#
# Copyright (c) 2011, EPFL (Ecole Politechnique Federale de Lausanne)
# All rights reserved.
#
# Created by Marco Canini, Daniele Venzano, Dejan Kostic, Jennifer Rexford
# Contributed to this file: Peter Peresini, Maciej Kuzniar
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

import sys
import copy

from of_controller import Controller
from lib.node import Node
from lib.of_context import Context
from nox.lib import openflow

import utils

import logging
log = logging.getLogger("nice.mc.ctrl")

class NOXController(Controller, Node):
    """Interface for a controller implementation"""
    def __init__(self, component_class, name="ctrl", max_callbacks=0):
        Node.__init__(self, name, 0)
        ctxt = Context(self)
        self.component_object = component_class(ctxt=ctxt)
        self.connection_count = 0
        self.in_connections = {}
        self.callbacks = []
        self.start_callbacks = []
        self.max_callbacks = max_callbacks

    @property
    def component(self):
        self.communicationObjectUsed(self, "ctrl_component")
        return self.component_object

    def start(self, model_checker):
        Node.start(self, model_checker)
        for callback in self.start_callbacks:
            callback()
        self.start_callbacks = None

    def install(self):
        self.component.install()

    def enqueueQuery(self, dp_id, buffer_id, packet, inport, reason):
        pkt_cpy = None if packet is None else packet.copy()
        self.in_connections[dp_id][1].append((buffer_id, pkt_cpy, inport, reason))
        self.enableAction("process_switch_query", dp_id, skip_dup=True)

    def portStatsRequest(self, dp_id, ports):
        self.enableAction("port_stats_special", (dp_id))

    def port_stats_special(self, dp_id):
        return True

    def port_stats(self, dp_id, stats):
        self.model_checker.strategy.beginControllerCallback()
        self.component.port_stats_in_cb(dp_id, copy.deepcopy(stats))
        self.enabled_actions[:] = [x for x in self.enabled_actions if x.target != "port_stats"]
        self.model_checker.strategy.endControllerCallback()
        return False

    def port_status(self, dp_id, reason, port):
        self.model_checker.strategy.beginControllerCallback()
        if self.component.port_status_cb != None:
            self.component.port_status_cb(dp_id, reason, port)
        self.model_checker.strategy.endControllerCallback()
        return True

    def postCallback(self, time, callback):
        if (len(self.callbacks) >= self.max_callbacks):
            # sorry, too many callbacks
            return
        callback_name = callback.__name__
        if callback_name in self.callbacks:  # we keep only the name, so do not register the same callback twice
            return 
        self.enableAction("process_callback", len(self.callbacks))
        self.callbacks.append(callback_name)

    def process_callback(self, callback_id):
        self.model_checker.strategy.beginControllerCallback()
        # for now do not erase old callbacks, it is not worth it, the list is small anyway
        callback_name = self.callbacks[int(callback_id)]
        if hasattr(self.component, callback_name):
            getattr(self.component, callback_name)()
        self.model_checker.strategy.endControllerCallback()
        return True

    def process_switch_query(self, dp_id):
        self.model_checker.strategy.beginControllerCallback()
        if not self.in_connections.has_key(dp_id):
            return True
        buffer_id, packet, inport, reason = self.in_connections[dp_id][1].pop(0)
        self.state.testPoint("before_cnt_packet_in", buffer_id=buffer_id, packet=packet, inport=inport, reason=reason, dp_id=dp_id)
        length = 0
        result = self.component.packet_in_cb(dp_id, inport, reason, length, buffer_id, packet)
        self.state.testPoint("after_cnt_packet_in", controller=self.component, packet=packet, return_value=result, dp_id=dp_id)
        if reason == openflow.OFPR_ACTION:
            self.state.testPoint("packet_received", receiver=self, packet=packet, port=inport)

        # NOTE: this code is specific to the loadbalancer
        if isinstance(self, LoadBalancerController) and self.callback0_count < 2:
            if packet.type == packet.ARP_TYPE and packet.dst == (0x11, 0x22, 0x33, 0x44, 0x55, 0x66):
                self.enableAction("process_callback", 0, skip_dup=True)
                self.count_packets += 1

        self.model_checker.strategy.endControllerCallback()
        return len(self.in_connections[dp_id][1]) == 0

    def addSwitch(self, switch):
        """ Note: this is not an action, but it should be """
        self.model_checker.strategy.beginControllerCallback()
        # pass empty statistics when a new switch is connected
        stats = {'ports' : []}
        if self.component.datapath_join_cb != None:
            self.component.datapath_join_cb(switch.getOpenflowID(), stats)
        self.in_connections[switch.getOpenflowID()] = (switch, [])
        self.connection_count += 1
        self.model_checker.strategy.endControllerCallback()

    def delSwitch(self, switch):
        self.enableAction("datapath_leave", (switch.getOpenflowID(),))

    def datapath_leave(self, dpid):
        self.model_checker.strategy.beginControllerCallback()
        if self.component.datapath_leave_cb != None:
            self.component.datapath_leave_cb(dpid)
        if self.in_connections.has_key(dpid):
            del self.in_connections[dpid]
        self.connection_count -= 1
        self.model_checker.strategy.endControllerCallback()
        return True

    def isSameMicroflow(self, packet1, packet2):
        raise NotImplementedError

    def dump_equivalent_state(self):
        filtered_dict = Node.dump_equivalent_state(self)
        filtered_dict["component"] = utils.copy_state(self.component)

        filtered_dict["in_connections"] = {}
        keys = self.in_connections.keys()
        keys.sort()
        for j in keys:
            filtered_dict["in_connections"][j] = []
            for m in self.in_connections[j][1]:
                filtered_dict["in_connections"][j].append(utils.copy_state(m)) # get only the buffer

        return filtered_dict

    def getControllerAppState(self):
        return self.component.dump_equivalent_state()

    def process_packet(self):
        raise NotImplementedError

    def packetLeftNetworkHandler(self):
        pass

    def flowRemoved(self, msg):
        self.enableAction("flow_removed", msg)

    def flow_removed(self, msg):
        self.model_checker.strategy.beginControllerCallback()
        if self.component.flow_removed_cb != None:
            self.component.flow_removed_cb(self, msg)
        self.model_checker.strategy.endControllerCallback()
        return True

class PySwitchController(NOXController):
    """A pyswitch controller"""
    def __init__(self, version="pyswitch"):
        self.mod = None
        if version == "pyswitch":
            import pyswitch.pyswitch as pyswitch_mod
            self.mod = pyswitch_mod
            NOXController.__init__(self, pyswitch_mod.pyswitch)
        elif version == "wildswitch":
            import wildswitch.wildswitch as wildswitch_mod
            self.mod = wildswitch_mod
            NOXController.__init__(self, wildswitch_mod.wildswitch)
        else:
            assert False

    def isSameMicroflow(self, packet1, packet2):
        if set([packet1.src, packet1.dst]) & set([packet2.src, packet2.dst]):
            return True
        return False

    def __repr__(self):
        return str(self.component)

class EateController(NOXController):
    def __init__(self, version):
        eate_mod = __import__("eate_app." + version)
        eate_mod = getattr(eate_mod, version)
        NOXController.__init__(self, eate_mod.eate)

    def start(self, model_checker):
        NOXController.start(self, model_checker)
#       self.enableAction("port_stats_special", (1))

    def packetLeftNetworkHandler(self):
        self.enableAction("port_stats_special", (1))

    def isSameMicroflow(self, packet1, packet2):
        return (packet1.src == packet2.src and packet1.dst == packet2.dst)
            


class LoadBalancerController(NOXController):
    MOD_LIST = ["lbtest", "Alphas", "Arps",
            "Bins", "EvalRules", "Globals",
            "IPRules", "IPs", "IPTransition",
            "Multipath", "Stats"]

    CONF_0 = "1, 3\n2, 1"
    CONF_1 = "1, 1\n2, 3"

    def __init__(self, use_fixed=False):
        if use_fixed:
            self.package = "loadbalancer.loadbalancer_fixed_"+use_fixed+"."
        else:
            self.package = "loadbalancer.loadbalancer."
        self.modules = []
        for i in range(0, len(self.MOD_LIST)):
                self.modules.append(self.package + self.MOD_LIST[i])

        self.callback0_count = 0
        self.count_packets = 0
        if self.package + "lbtest" in sys.modules:
            for m in self.modules:
                reload(sys.modules[m])
            lb_mod = sys.modules[self.package + "lbtest"]
        else:
            lb_mod = __import__(self.package)
            lb_mod = getattr(lb_mod, self.package.split(".")[1])
            lb_mod = lb_mod.lbtest

        sys.modules[self.package + "Globals"].ALPHAFILE = self.CONF_0
        NOXController.__init__(self, lb_mod.lbtest, max_callbacks=2)

    def setConfigFile(self):
        if self.callback0_count > 1:
            return
        elif self.callback0_count == 0:
            self.callback0_count = 1
            sys.modules[self.package + "Globals"].ALPHAFILE = self.CONF_0
        elif self.callback0_count == 1:
            self.state.testPoint("reload_config")
            self.callback0_count = 2
            sys.modules[self.package + "Globals"].ALPHAFILE = self.CONF_1

    def postCallback(self, time, callback):
        if (len(self.callbacks) >= self.max_callbacks):
            # too many callbacks
            return
        self.callbacks.append(callback)
        if len(self.callbacks) == 1: # callback is the alphaFileUpdate
            return # delayed
        else: # callback is the arpRequestReplicas
            self.enableAction("process_callback", 1)

    def process_callback(self, callback_id):
        self.model_checker.strategy.beginControllerCallback()
        # for now do not erase old callbacks, it is not worth it, the list is small anyway
        if callback_id == 0:
            self.setConfigFile()

        self.callbacks[int(callback_id)]()
        self.model_checker.strategy.endControllerCallback()

        if self.callback0_count == 1 and self.count_packets == 2:
            return False
    
        return True

    def isSameMicroflow(self, packet1, packet2):
        tcp_pkt1 = packet1.find("tcp")
        tcp_pkt2 = packet2.find("tcp")
        if tcp_pkt1 == None or tcp_pkt2 == None:
            return (packet1.src == packet2.src and packet1.dst == packet2.dst)
        else:
            return tcp_pkt1.flow_id == tcp_pkt2.flow_id

