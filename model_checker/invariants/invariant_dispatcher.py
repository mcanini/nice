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

import time, copy
import utils
import logging
log = logging.getLogger("nice.inv")

from invariants.return_continue_stop import ReturnContinueStop
from invariants.no_drop_invariant import NoDropInvariant
from invariants.no_forgotten_packets import NoForgottenPackets

class InvariantDispatcher:
    TIME_START = time.time()
    DEFAULT_INVARIANTS = [ReturnContinueStop, NoDropInvariant, NoForgottenPackets]

    def __init__(self, model_checker):
        self.model_checker = model_checker
        self.new_violations = False
        self.invariants = []
        self.violation_counter = {}
        self.new_violation_path = False
        for i in self.DEFAULT_INVARIANTS:
            self.registerInvariant(i)

    def registerInvariant(self, inv_class):
        i = inv_class()
        i.updateDispatcher(self)
        self.violation_counter[i.name] = [0, 0, 0, None]
        self.invariants.append(i)

    def testPoint(self, event_name, **args):
        for i in self.invariants:
            if hasattr(i, event_name + "_cb"):
                method = getattr(i, event_name + "_cb")
                try:
                    method(**args)
                except TypeError:
                    utils.crash("Invariant '%s', callback '%s' has wrong arguments. Passing %s" % (i.name, event_name+"_cb", str(args)))

    def reportViolation(self, violation):
        if violation.is_fatal:
            self.new_violations = True
        violation.time_elapsed = violation.timestamp - self.TIME_START
        violation.transitions = self.model_checker.good_transitions_count
        violation.unique_states = len(self.model_checker.unique_states)

        if self.violation_counter[violation.invariant_name][0] == 0:
            self.violation_counter[violation.invariant_name] = [1, violation.time_elapsed, violation.transitions, None]
            self.new_violation_path = True
        else:
            self.violation_counter[violation.invariant_name][0] += 1
        # NOTE we use little information from all there is in a violation object
        # NOTE there could be a dedicated log file or even a database and a tool
        # NOTE to help visualizing the path that led to the violation
        log.error("Invariant violation: " + repr(violation))
        if self.model_checker.state_debug:
            log.error(self.model_checker.state.replay_list)

    def checkNewViolations(self, state):
        ret = self.new_violations
        if self.model_checker.state_debug and self.new_violation_path:
            for violation in self.violation_counter:
                if self.violation_counter[violation][3] is None:
                    self.violation_counter[violation][3] = state.replay_list
        self.new_violation_path = False
        self.new_violations = False
        return ret

    def countViolations(self):
        return sum([x[0] for x in self.violation_counter.values()])

    def serializedState(self):
        inv_dict = {}
        for i in sorted(self.invariants):
            inv_dict[i.name] = utils.copy_state(i)
        return utils.copy_state(inv_dict)

    def __deepcopy__(self, memo):
        c = InvariantDispatcher(self.model_checker)
        memo[id(self)] = c
        d = c.__dict__
        for k in self.__dict__:
            if k == "model_checker":
                continue
            elif k == "violation_counter":
                d[k] = self.violation_counter
                continue
            try:
                d[k] = copy.deepcopy(self.__dict__[k], memo)
            except RuntimeError:
                utils.crash(k)

        for i in c.invariants:
            i.updateDispatcher(c)

        return c

