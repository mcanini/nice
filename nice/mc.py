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
import multiprocessing

import logging
log = logging.getLogger("nice.mc")
log_stats = logging.getLogger("stats")
import utils
from stats import getStats
stats = getStats()
import config_parser as config

MODEL_CHECKER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../model_checker"))

class ModelCheckerProcess(multiprocessing.Process):
    def __init__(self, queues):
        multiprocessing.Process.__init__(self, group=None, target=self.model_check)
        self.queues = queues

    def model_check(self):
        stats.reset()

        sys.path = [MODEL_CHECKER_DIR, os.path.join(MODEL_CHECKER_DIR, "nox_lib")] + sys.path

        sys.stdin = open("/dev/stdin", "r") # multiprocess closes it
        if config.get("runtime.debug_mc"):
            from lib.model_checker import DebugModelChecker
        else:
            from lib.model_checker import ModelChecker
        from lib.strategies import strategies, RandomWalk
        from models import models

        if not models.has_key(config.get("model.name")):
            utils.crash("Invalid model name: " + config.get("model.name") + ".\nValid model names are: "+ ', '.join(models.keys()))

        if not strategies.has_key(config.get("strategy.name")):
            utils.crash("Invalid strategy name: " + config.get("strategy.name") + ".\nValid strategy names are: "+ ', '.join(strategies.keys()))

        config.set("model.class", models[config.get("model.name")])
        config.set("strategy.class", strategies[config.get("strategy.name")])

        stats.pushProfile("model checker init")
        symbolic_options = {"queues": self.queues}

        if config.get("runtime.debug_mc"):
            mc = DebugModelChecker(symbolic_options)
        else:
            mc = ModelChecker(symbolic_options)

        stats.popProfile()

        try:
            stats.pushProfile("model checker run")
            mc.start()
        except KeyboardInterrupt:
            log_stats.error("INTERRUPTED!")
        except:
            print sys.exc_info()[1]
        finally:
            stats.popProfile()

            log_stats.info("--- Profiling info for model checker ---")
            log_stats.info("\n" + stats.getProfilingOutput())
            log_stats.info("--- Results ---")
            log_stats.info("Total states: %d" % (len(mc.unique_states) + mc.old_states_count))
            log_stats.info("Unique states: %d" % len(mc.unique_states))
            log_stats.info("Revisited states: %d" % mc.old_states_count)
            log_stats.info("Maximum path length: %d" % mc.max_path_length)
            log_stats.info("Invariant violations: %d" % sum([x[0] for x in mc.violation_counter.values()]))

            for k in mc.violation_counter:
                if mc.violation_counter[k][0] == 0:
                    log_stats.debug("%-30s: 0 violations" % k)
                else:
                    violation = mc.violation_counter[k]
                    log_stats.error("%-30s: %d violations (first found after %.2fs, %d transitions)" % (k, violation[0], violation[1], violation[2]))
                    if violation[3]:
                        log_stats.error("PATH: %s" % violation[3])

            if config.get("runtime.graph") is not None:
                mc.graph.saveToFile()

            if config.get("strategy.class") == RandomWalk:
                log_stats.warning("Random walk seed: %d", mc.strategy.seed)

