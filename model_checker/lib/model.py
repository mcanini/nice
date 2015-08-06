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

import pprint

from lib.action import Action
import utils

import logging
log = logging.getLogger("nice.mc.model")
from stats import getStats
stats = getStats()
import config_parser as config

class Model:
    generate_inputs = False
    generate_stats = False
    invariants = []

    def __init__(self):
        # entities in the topology
        self.switches = []
        self.switches_idx = {}
        self.controller = None
        self.clients = []
        self.nodes = {} # Keep track of nodes by their name because references are not stable
        self.fault_injection_count = 0
        self.switch_failures_count = 0
        self.packet_counters = {} # used to generate packet IDs
        self.actionList = []
        self.useDpor = False;

    def initTopology(self, topo):
        raise NotImplementedError

    def decFaultInjectionCount(self):
        self.fault_injection_count -= 1
        for s in self.switches:
            s.setFaultInjectionCount(self.fault_injection_count)

    def setFaultInjectionCount(self, num_faults):
        self.fault_injection_count = num_faults
        for s in self.switches:
            s.setFaultInjectionCount(num_faults)

    def setSwitchFailuresCount(self, count):
        self.switch_failures_count = count

    def getNodes(self):
        objs = self.clients + self.switches
        if not self.controller is None:
            objs.append(self.controller)
        return objs

    def setState(self, state):
        for c in self.getNodes():
            c.state = state

    def start(self, model_checker):
        self.actionList = []
        self.useDpor = model_checker.useDpor;
        for c in self.getNodes():
            self.packet_counters[c.name] = 0
            self.nodes[c.name] = c
            c.start(model_checker)
        if config.get("model.switch_failures") and self.switch_failures_count > 0:
            for s in self.switches:
                s.enableFailure()

    def printEnabledActions(self):
        ena = self.getAllEnabledActions()
        log.debug("Enabled actions: %s" % ena)

    def getAllEnabledActions(self):
        actions = []
        for c in self.getNodes():
            actions += c.enabled_actions
        return actions

    def executeAction(self, action, depth):
        log.info("%d -- Executing action: %s" % (depth, str(action)))
        node = self.nodes[action.node_name]
        action2 = action;   
        if hasattr(node, "discover_packets") and action.target == "send_packet":
            action2 = Action(action.node_name, action.target, [])
        if action2 not in self.actionList:
            self.actionList.append(action2)
        node.runAction(action)

    def serializedState(self):
        state = self.nodesState()
        if self.useDpor:
            self.actionList.sort()
            state["actionList"] = utils.copy_state(self.actionList)
        state["fault_injection_count"] = utils.copy_state(self.fault_injection_count)
        state["switch_failures_count"] = utils.copy_state(self.switch_failures_count)
        state["packet_counters"] = utils.copy_state(self.packet_counters)
        state["useDpor"] = utils.copy_state(self.useDpor)
        return state

    def nodesState(self):
        serialized_state = {}
        for c in self.getNodes():
            serialized_state[c.name] = c.dump_equivalent_state()
        return serialized_state

    def __repr__(self):
#       s = pprint.pformat(self.nodesState())
        s = "<model instance>"
        return s

    def getControllerAppState(self):
        return self.controller.getControllerAppState()

    def getClientMacAddresses(self):
        l = []
        for c in self.clients:
            l.append(c.mymac.data)
        return l

