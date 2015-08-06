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

from of_controller import Controller
from of_switch.of_switch import OpenflowSwitch
from lib.strategies.strategy import Strategy

import logging
log = logging.getLogger("nice.mc.strategy")

CONST_DELAY = 4

class HeuristicConstCtrlDelay(Strategy):
    def __init__(self, model_checker):
        Strategy.__init__(self, model_checker)

    def getEnabledActions(self, state):
        actions = state.getAllEnabledActions()
        filtered_actions = []
        for a in actions:
            if a.delay == 0:
                filtered_actions.append(a)
            else:
                a.delay -= 1

        normal_actions = [x for x in filtered_actions if x.target not in ["move_host_", "duplicate_packet", "send_packet"]]
        #log.debug("Enabled priority actions: %s" % delayed_actions)
        if len(normal_actions) > 0:
            return filtered_actions
        else:
            min_delay = CONST_DELAY + 1
            min_action = None
            for a in actions:
                if (a not in filtered_actions) and (a.delay < min_delay):
                    min_delay = a.delay
                    min_action = a
            
            if min_action is None:
                return filtered_actions
            else:
                #preserve the order of actions
                return [x for x in actions if (x in filtered_actions) or (x.delay == min_delay)]


    def onEnableAction(self, node, action):
        priority = (isinstance(node, Controller) and action.target=="process_switch_query") or \
            (isinstance(node, OpenflowSwitch) and action.target=="process_command")
        if priority:
            action.delay = CONST_DELAY
            log.debug("Enabled delayed action %s" % str(action))
        else:
            action.delay = 0
        return action

    def chooseAction(self, state):
        action = state.available_actions.pop(0)
        return action

