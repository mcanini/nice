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

import os
import sys
import cPickle
import multiprocessing

import logging
log = logging.getLogger("nice.se")
log_stats = logging.getLogger("stats")
import utils
from stats import getStats
stats = getStats()
import config_parser as config

SE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../sym_exec"))
APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../nox_apps"))
INSTR_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "se_normalized"))

class SymbolicExecution(multiprocessing.Process):
    def __init__(self, queues):
        nox_app_dir = os.path.join(APP_DIR, config.get("model.app_dir"))
        app_args = ""
        args = (nox_app_dir, app_args)
        multiprocessing.Process.__init__(self, group=None, target=self.generate_new_inputs_, args=args)
        self.queue_inputs = queues[0]
        self.queue_states = queues[1]
        self.prepare_completed = False
        self.states_inputs_cache = {}

    def macTuple2Long(self, t):
        aux = long(0)
        aux = t[0] << 40
        aux |= t[1] << 32
        aux |= t[2] << 24
        aux |= t[3] << 16
        aux |= t[4] << 8
        aux |= t[5]
        return aux

    def prepare(self, nox_app_dir, app_args):
        from symbolic import preprocess

        nox_app_dir = os.path.abspath(nox_app_dir)

        if not os.path.exists(INSTR_DIR):
            os.mkdir(INSTR_DIR)

        preprocess.instrumentLibrary(os.path.join(SE_DIR, "sym_exec_lib"), INSTR_DIR)

        if config.get("model.app_descr") == None:
            return None

        # add the app directory to the import path, just to get the configuration
        tmp_import_dir = os.path.abspath(os.path.dirname(config.get("model.app_descr")))
        sys.path = [tmp_import_dir] + sys.path

        app_description = __import__("se_descr")

        # then remove it and put in the instrumented version directory
        sys.path.pop(0)

        # Get the object describing the application
        app_description = app_description.factory(app_args)

        log.info("Preparing concolic execution on " + app_description.APP_NAME)

        for m in app_description.NORMALIZE_MODS:
            preprocess.instrumentModule(m, INSTR_DIR, is_app=True, in_dir=nox_app_dir)
        for p in app_description.NORMALIZE_PACKAGES:
            preprocess.instrumentPackage(p, INSTR_DIR, in_dir=nox_app_dir)

        self.prepare_completed = True

        return app_description

    def generate_new_inputs_(self, nox_app_dir, app_args):
        try:
            self.generate_new_inputs(nox_app_dir, app_args)
        except KeyboardInterrupt:
            log.error("Symbolic engine interrupted!")

    def generate_new_inputs(self, nox_app_dir, app_args):
        sys.path = [SE_DIR, INSTR_DIR] + sys.path

        from symbolic.concolic import ConcolicEngine
        from symbolic import stp

        stats.reset()
        app_description = self.prepare(nox_app_dir, app_args)

        stats.newCounter("explorations")
        stats.pushProfile("symbolic engine")
        macs = []

        while True:
            state = self.queue_states.get()
            log.debug("State received")
            stats.pushProfile("state parsing")
            if state == "QUIT": # special message
                log.info("Symbolic engine quitting...")
                self.queue_states.task_done()
                stats.popProfile()
                break
            elif state == "INITIAL":
                log.info("Symbolic engine receiving initial state...")
                self.queue_states.task_done()
                l = self.queue_states.get()
                try:
                    l = int(l)
                except ValueError:
                    utils.crash("Model checker process is sending garbage")
                self.queue_states.task_done()
                macs = []
                for i in range(0, l):
                    m = self.queue_states.get()
                    m = cPickle.loads(m)
                    m = self.macTuple2Long(m)
                    macs.append(m)
                    if i != l-1:
                        self.queue_states.task_done()
                #log.debug("Generating initial inputs...")
                self.queue_states.task_done()
                continue

            log.debug("Generating new inputs...")
            if state in self.states_inputs_cache:
                log.debug("Using cached symbolic execution results")
                inputs = self.states_inputs_cache[state]
            else:
                (packet, app_state) = cPickle.loads(state)
                invocation_sequence = app_description.create_invocations(macs)
                invocation_sequence[0].setState(packet, app_state)

                stats.popProfile()
                stats.incCounter("explorations")

                # Init the concolic engine with the provided state
                engine = ConcolicEngine(False)
                engine.setInvocationSequence(invocation_sequence)
                engine.setResetCallback(app_description.reset_callback)

                # Run
                stats.pushProfile("concolic engine run")
                return_vals = engine.run()
                stats.popProfile()

                # Generate inputs
                inputs = engine.generated_inputs
                log.info("Generated %d new inputs" % len(inputs))
                inputs = cPickle.dumps(inputs, -1)
                self.states_inputs_cache[state] = inputs
                log.debug("cache size: %d" % len(self.states_inputs_cache))
#               if len(self.states_inputs_cache) > 500: # have a maximum
#                   to_del = random.sample(xrange(500), 100)
#                   for e in to_del:
#                       k = self.states_inputs_cache.keys()[e]
#                       del self.states_inputs_cache[k]

            # send the new inputs to the model checker
            self.queue_inputs.put(inputs)
            self.queue_states.task_done()

            app_description.execution_complete(return_vals)
            stp.resetVarCache()

        stats.popProfile()
        if stats.counters["explorations"] > 0:
            log_stats.info("--- Profiling info for symbolic execution ---")
            log_stats.info("\n" + stats.getProfilingOutput())

            log_stats.info("--- Counters for symbolic execution ---")
            log_stats.info("\n" + stats.getCounterOutput())

