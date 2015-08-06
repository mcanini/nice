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

from symbolic_interpreter import SymbolicInterpreter
from python_tracer import PythonTracer
from symbolic import instrumentation
from collections import deque

import logging
log = logging.getLogger("nice.se.conc")

from stats import getStats
stats = getStats()

class ConcolicEngine:
    PYTHON_FUNCTION_INVOCATIONS = 0

    def __init__(self, debug):
        self.constraints_to_solve = deque([])
        self.num_negated_constraints = 0
        self.interpreter = SymbolicInterpreter(self)
        instrumentation.SI = self.interpreter
        self.execution_return_values = []
        self.reset_func = None
        self.tracer = PythonTracer(debug)
        self.tracer.setInterpreter(self.interpreter)
        self.interpreter.setTracer(self.tracer)
        self.invocation_sequence = None
        stats.newCounter("explored paths")
        self.generated_inputs = []

    def setResetCallback(self, reset_func):
        self.reset_func = reset_func

    def setInvocationSequence(self, sequence):
        self.invocation_sequence = sequence

    def addConstraint(self, constraint):
        self.constraints_to_solve.append(constraint)

    def isExplorationComplete(self):
        num_constr = len(self.constraints_to_solve)
        if num_constr == 0:
            log.info("Exploration complete")
            return True
        else:
            log.info("%d constraints yet to solve (total: %d, already solved: %d)" % (num_constr, self.num_negated_constraints + num_constr, self.num_negated_constraints))
            return False

    def execute(self, invocation_sequence):
        self.reset_func()
        return_values = []
        stats.incCounter("explored paths")
        log.info("Iteration start")
        stats.pushProfile("single iteration")
        for invocation in invocation_sequence:
            invocation.setupTracer(self.tracer)
            stats.pushProfile("single invocation")
            res = self.tracer.execute()
            stats.popProfile()
            return_values.append(res)
            log.info("Invocation end")

        stats.popProfile()
        log.info("Iteration end")
        return return_values

    def run(self, max_iterations=0):
        # first iteration, find some constraints to bootstrap with
        ret = self.execute(self.invocation_sequence)
        self.execution_return_values.append(ret)
        iterations = 1
        concr_inputs = {}
        for k in self.invocation_sequence[0].symbolic_inputs:
            concr_inputs[k] = self.invocation_sequence[0].symbolic_inputs[k].getConcrValue()
        self.generated_inputs.append(concr_inputs)

        if max_iterations != 0 and iterations >= max_iterations:
            log.debug("Maximum number of iterations reached, terminating")
            return self.execution_return_values

        while not self.isExplorationComplete():
            selected = self.constraints_to_solve.popleft()
            if selected.negated:
                continue

            self.interpreter.newExecution()

            log.info("Soving constraint %s" % selected)
            stats.pushProfile("constraint solving")
            ret = selected.negateConstraint(self.tracer.execution_context)
            stats.popProfile()
            if not ret:
                log.warning("Unsolvable constraints, skipping iteration")
                iterations += 1
                continue

            concr_inputs = {}
            for k in self.invocation_sequence[0].symbolic_inputs:
                concr_inputs[k] = self.invocation_sequence[0].symbolic_inputs[k].getConcrValue()
            self.generated_inputs.append(concr_inputs)

            ret = self.execute(self.invocation_sequence)
            self.execution_return_values.append(ret)
            iterations += 1
            
            self.num_negated_constraints += 1

            if max_iterations != 0 and iterations >= max_iterations:
                log.debug("Maximum number of iterations reached, terminating")
                break

        return self.execution_return_values

