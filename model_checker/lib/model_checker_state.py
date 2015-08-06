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

USE_MD5 = False

from pprint import pprint, pformat
import json, copy
if USE_MD5:
    import hashlib

import logging
log = logging.getLogger("nice.mc.state")

from stats import getStats
stats = getStats()
import utils

import config_parser as config

class ModelCheckerState:
    def __init__(self, model, inv_dis, setState = True):
        self.model = model
        self.invariant_dispatcher = inv_dis
        self.replay_list = []
        self.state_replay_list = [] # used only when replay debugging is active
        self.state_id = utils.getID("state") # only to recognize state in debug output
        self.available_actions = []
        if setState:
            self.model.setState(self)
        self.path_length = 0
        self.strategy_state = None
        # defer hashing

    def hasAvailableActions(self):
        return len(self.available_actions) > 0

    def setAvailableActions(self, actions):
        self.available_actions = actions

    def getAllEnabledActions(self):
        return self.model.getAllEnabledActions()

    def executeAction(self, action, counter, is_replaying=False):
        self.model.executeAction(action, counter)
        for h in self.model.clients:
            if hasattr(h, "enableDiscoveryIfNeeded"):
                h.enableDiscoveryIfNeeded(self)
        if config.get("runtime.replay") and not is_replaying:
            self.replay_list += [action]
        self.path_length += 1

    def testPoint(self, e, **args):
        self.invariant_dispatcher.testPoint(e, model=self.model, **args)

    def checkNewViolations(self):
        return self.invariant_dispatcher.checkNewViolations(self)

    def reportViolation(self, *args):
        self.invariant_dispatcher.reportViolation(*args)

    def copy(self, get_app_state=True):
#       import pdb; pdb.set_trace()
        stats.pushProfile("state copying")
        memo = { "get_app_state": get_app_state } # Dirty trick
        m = copy.deepcopy(self.model, memo)
        i = copy.deepcopy(self.invariant_dispatcher, memo)
        c = ModelCheckerState(m, i)
        if config.get("runtime.replay"):
            c.replay_list = self.replay_list[:]
            c.state_replay_list = self.state_replay_list[:]
        c.path_length = self.path_length
        c.available_actions = self.available_actions[:]
        c.strategy_state = copy.deepcopy(self.strategy_state, memo)
#       if hash(self) != hash(c):
#           utils.crash("Different hashes after state copy")
        stats.popProfile()
        return c

    def minimal_copy(self, get_app_state=True):
        """ copies only the state required to do the replay """
        stats.pushProfile("shallow state copying")
        c = ModelCheckerState(None, None, False)
        if config.get("runtime.replay"):
            c.replay_list = self.replay_list[:]
            c.state_replay_list = self.state_replay_list[:]
        c.path_length = self.path_length
        c.available_actions = self.available_actions[:]
        stats.popProfile()
        return c

    def restoreState(self, strategy=None):
        self.model.controller.component.install()
        if (strategy is not None) and (self.strategy_state is not None):
            strategy.loadState(self.strategy_state)
            strategy.visitModel(self.model)
        if hasattr(self.model.controller.component, "restore_state"):
            self.model.controller.component.restore_state()
    
    def storeState(self, strategy):
        self.strategy_state = strategy.dumpState()
        if hasattr(self.model.controller.component, "store_state"):
            self.model.controller.component.store_state()

    def __hash__(self):
        return self._serializeAndHash()

    def _getEqState(self):
        model_eq_state = self.model.serializedState()
        invariants_eq_state = self.invariant_dispatcher.serializedState()
        return [model_eq_state, invariants_eq_state]

    def _serializeAndHash(self):
        stats.pushProfile("state serialization1")
        eq_state = self._getEqState()
        stats.popProfile()
        stats.pushProfile("state serialization2")
        ser_state = json.dumps(eq_state, -1)
        stats.popProfile()

        stats.pushProfile("state hashing")
        if USE_MD5:
            h = hashlib.md5()
            h.update(ser_state)
            h = int(h.hexdigest(), 16)
        else:
            h = hash(ser_state)
        stats.popProfile()
        return h

    def __eq__(self, other):
        if other is None:
            return False
        if config.get("runtime.replay_debug"):
            return self._debugCompareStates(other)
        else:
            return hash(self) == hash(other)

    def __ne__(self, other):
        if other is None:
            return True
        if config.get("runtime.replay_debug"):
            return not self._debugCompareStates(other)
        else:
            return hash(self) != hash(other)

    def _debugCompareStates(self, other):
        eq_state = self._getEqState()
        other_eq_state = other._getEqState()
        ret = True
        for i in [0]: # 0: nodes, 1: invariants
            for k in eq_state[i]:
                s = eq_state[i][k]
                o = other_eq_state[i][k]
                if s != o:
                    log.error("State of %s is different" % k)
                    log.error("self")
                    pprint(s)
                    log.error("other")
                    pprint(o)
                    ret = False
        return ret

    def __repr__(self):
        s = "State ID: %d\n" % self.state_id
        if config.get("runtime.replay"):
            s += "  replay_list: %s\n" % self.replay_list
        s += "  available_actions: %s" % self.available_actions
        s += pformat(self.model)
        return s

