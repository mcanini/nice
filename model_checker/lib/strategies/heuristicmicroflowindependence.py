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

import types
import copy

from of_controller import Controller
from lib.strategies.strategy import Strategy

import logging
log = logging.getLogger("nice.mc.strategy")

ctxt = None

class HeuristicMicroFlowIndependence(Strategy):
    def __init__(self, model_checker):
        global ctxt
        Strategy.__init__(self, model_checker)
        self.cur_flow = 0
        self.ctrl = None
        self.flows = [None]
        ctxt = self

    def getEnabledActions(self, state):
        actions = state.getAllEnabledActions()
        if not actions:
            return actions

        filtered_actions = []
        next_cur_flow = -1
        for a in actions:
            if a.flow is not None and a.flow > 0:
                next_cur_flow = a.flow
                break

        for a in actions:
            if a.flow is None or a.flow == next_cur_flow:
                filtered_actions.append(a)
       
        return filtered_actions
    
    def onEnableAction(self, node, action):
        action.flow = self.cur_flow
        if self.cur_flow == 0 or action.target not in ["process_packet", "process_command", "process_switch_query"]:
            action.flow = None
        return action
    
    def beforeReplayAction(self, action):
        if action.flow is not None:
            self.cur_flow = action.flow
        else:
            self.cur_flow = 0

    def chooseAction(self, state):
        action = state.available_actions.pop(0)
        self.beforeReplayAction(action)
        return action

    def visitModel(self, model):
        self.ctrl = None
        for n in model.getNodes():
            log.debug("microflow %s" % str(n.__class__))
            n.enqueuePacket = types.MethodType(enqueuePacket, n, n.__class__)
            if isinstance(n, Controller):
                if not self.ctrl is None:
                    raise NotImplementedError
                self.ctrl = n
                if not hasattr(n, "enqueueQueryOriginal"):
                    n.enqueueQueryOriginal = n.enqueueQuery
                    n.enqueueQuery = types.MethodType(enqueueQuery, n, n.__class__)

    def trackMicroflow(self, packet):
        # check packet independence to other active flows
        self.cur_flow = -1
        for idx, f in enumerate(self.flows[1:]):
            if self.ctrl.isSameMicroflow(packet, f):
                # if dep reuse the correct cur_flow
                self.cur_flow = idx + 1
                return
        # if a client sending a new packet or indep, assign a new cur_flow, mark all new enabled actions with new microflow
        log.debug("new microflow %s" % str(packet))
        self.flows.append(packet)
        self.cur_flow = len(self.flows) - 1

    def dumpState(self):
        d = {}
        d["cur_flow"] = self.cur_flow
        return d

    def loadState(self, d):
        self.cur_flow = d["cur_flow"]
        
def enqueuePacket(self, packet, inport):
    log.debug("microflow enqueuePacket")
    ctxt.trackMicroflow(packet)
    self.ports[inport].queueIn(packet)
    self.enableAction("process_packet", skip_dup=True)

def enqueueQuery(self, dp_id, buffer_id, packet, inport, reason):
    log.debug("microflow enqueueQuery")
    ctxt.trackMicroflow(packet)
    self.enqueueQueryOriginal(dp_id, buffer_id, packet, inport, reason)
