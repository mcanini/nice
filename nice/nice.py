#!/usr/bin/python
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

import sys, os
from optparse import OptionParser
import logging
import multiprocessing # used to keep the import paths (nox API in particular) distinct between nice.se and nice.mc
import time

sys.path = [os.path.abspath(os.path.join(os.path.dirname(__file__), "../common_modules")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "../nox_apps"))] + sys.path

import logger

import config_parser as config
import sym_exec
import mc

from stats import getStats
stats = getStats()

print "NICE (No Bugs In controller Execution): systematic testing of OpenFlow controller programs"

usage = "usage: %prog [options] <config.conf>"
parser = OptionParser(usage=usage)
parser.add_option("-l", "--log", dest="logfile", action="store", help="Save log output to a file", default="stdout")
parser.add_option("-g", "--graph", dest="graph", action="store", help="Save the DOT graph in the specified filename", default="none")
parser.add_option("-q", "--quiet", dest="quiet", action="store_true", help="Run quietly", default=False)
parser.add_option("-t", "--test", dest="test", action="store_true", help="Keep doing RandomWalks until an exception is raised", default=False)
parser.add_option("-p", "--progress", dest="progress", action="store_true", help="Like -q, but print progress information on stdout", default=False)
parser.add_option("-d", "--debug", dest="debug_mc", action="store_true", help="Use the debug ModelChecker", default=False)
parser.add_option("-R", "--replay", dest="replay", action="store_true", help="Enable state replay during model checking", default=False)
parser.add_option("-r", "--replay-debug", dest="debug_rep", action="store_true", help="Enable replay debug during model checking", default=False)

(options, args) = parser.parse_args()

if len(args) == 0:
    print "Missing config file as last parameter"
    sys.exit(1)

config.init(args[0])

# Copy command line options in the runtime section of the config file
config.set("runtime.debug_mc", options.debug_mc)
config.set("runtime.progress", options.progress)
config.set("runtime.quiet", options.quiet)
config.set("runtime.test", options.test)
config.set("runtime.logfile", options.logfile)
config.set("runtime.graph", options.graph)
config.set("runtime.replay", options.replay)
if options.debug_rep and options.replay:
    config.set("runtime.replay_debug", options.debug_rep)
else:
    config.set("runtime.replay_debug", False)
if options.debug_mc:
    config.set("runtime.log_level", logging.DEBUG)
if options.quiet:
    config.set("runtime.log_level", logging.CRITICAL)
if config.get("runtime.progress"):
    config.set("runtime.log_level", logging.CRITICAL)

config.convertTypes()

logger.init(config.get("runtime.logfile"), config.get("runtime.log_level"))
log = logging.getLogger("nice")

try:
    os.mkdir("se_normalized")
except:
    pass

def run():
    stats.pushProfile("NICE execution")

    # Nox app states from the modelchecker to the symolic engine
    # Input packets from the symbolic engine to the model checker
    queue_inputs = multiprocessing.JoinableQueue()
    queue_states = multiprocessing.JoinableQueue()

    try:
        nice_se = sym_exec.SymbolicExecution((queue_inputs, queue_states))
        nice_se.start()

        nice_mc = mc.ModelCheckerProcess((queue_inputs, queue_states))
        nice_mc.start()

        while nice_se.is_alive() and nice_mc.is_alive():
            time.sleep(0.05)

        if not nice_se.is_alive(): # symbolic engine crash
            log.critical("Symbolic engine crash")
            nice_se.join()
            nice_mc.terminate()
            nice_mc.join()
        else: # clean termination or model checker crash
            nice_mc.join()
            queue_states.put("QUIT")
            queue_states.join()
            nice_se.join()
    except KeyboardInterrupt:
        pass

    stats.popProfile()

    log_stats = logging.getLogger("stats")
    log_stats.info("\n" + stats.getProfilingOutput())

if options.test:
    config.set("strategy.name", "RandomWalk")
    while True:
        try:
            run()
        except:
            import traceback
            traceback.print_exc()
            log.critical("Random seed: %s" % str(options.seed))
            break
        time.sleep(1) # new seed
else:
    run()

