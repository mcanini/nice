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
import signal
import random
import cPickle
import platform
import time
import logging
log = logging.getLogger("nice.mc")
from pprint import pprint

from lib.action import Action
from lib.strategies import RandomWalk
from lib.strategies.dpor import DynamicPartialOrderReduction
from lib.model_checker_state import ModelCheckerState
from invariants.invariant_dispatcher import InvariantDispatcher

from stats import getStats
stats = getStats()
import utils
import config_parser as config

# Memory profiling (needs the objgraph library)
MEMORY_PROFILING = False
import gc, objgraph, inspect

class ModelChecker:
    def __init__(self, symbolic_options):
        self.model_class = config.get("model.class")
        self.strategy_class = config.get("strategy.class")
        self.strategy = None
        self.useDpor = config.get("strategy.dpor")
        self.dpor = None
        self.good_transitions_count = 0
        self.state_stack = None
        self.unique_states = set()
        self.old_states_count = 0
        self.max_path_length = 0
        self.total_last_sec = 0
        self.sym_engine_call_count = 0
        self.start_time = None
        self.state = None
        self.state_debug = config.get("runtime.replay_debug")
        if self.strategy_class == RandomWalk:
            if config.get("randomwalk.seed") == -1:
                self.random_seed = int(time.time())
            else:
                self.random_seed = config.get("randomwalk.seed")
        if config.get("runtime.graph") != None:
            from model_checker_graph import ModelCheckingGraph
            self.graph = ModelCheckingGraph(config.get("runtime.graph"), self)
        else:
            self.graph = None

        self.initial_inputs = []
        self.initial_state = None

        self.queue_inputs = symbolic_options["queues"][0]
        self.queue_states = symbolic_options["queues"][1]
        self.generate_inputs = self.model_class.generate_inputs
        self.generate_stats = self.model_class.generate_stats

        self.contr_app_states_stats = {} # States we already explored symbolically for stats

        self.packetTranslator = None

        self.violation_counter = None

        if config.get("runtime.progress"):
            print "MC init complete"

    def loadInitialInputs(self, inputs):
        self.initial_inputs = inputs

    def initializeSE(self, state):
        self.sym_engine_call_count += 1
        self.queue_states.put("INITIAL")
        self.queue_states.join()
        self.sendMacsToSymExec(state.model.getClientMacAddresses())
        self.queue_states.join()

    def generateInputs(self, state):
        self.sym_engine_call_count += 1
        self.queue_states.put(state)
        self.queue_states.join()
        inputs = self.queue_inputs.get()
        inputs = cPickle.loads(inputs)
        return inputs

    def generatePortStats(self, state):
        assert state != "INITIAL"
        self.sym_engine_call_count += 1
        self.queue_states.put(state)
        self.queue_states.join()
        inputs = self.queue_inputs.get()
        inputs = cPickle.loads(inputs)
        return inputs

    def sendMacsToSymExec(self, macs):
        l = len(macs)
        self.queue_states.put(l)
        self.queue_states.join()
        for m in macs:
            self.queue_states.put(cPickle.dumps(m), -1)
            self.queue_states.join()

    def start(self):
        self.start_time = time.clock()
        self.strategy = self.strategy_class(self)
        if self.useDpor:
            self.dpor = DynamicPartialOrderReduction(self, self.strategy)

        if isinstance(self.strategy, RandomWalk):
            self.strategy.setSeed(self.random_seed)
        if config.get("runtime.progress") and not platform.system() == 'Windows':
            signal.signal(signal.SIGALRM, self.printStats)
            signal.setitimer(signal.ITIMER_REAL, 0.1, 1)
        state = self.gotoInitialState()
        state.restoreState()
        if self.queue_states is not None:
            self.initializeSE(state)
        self.state_stack = [state]
        self.modelCheck()

    def getEnabledActions(self, state):
        return self.strategy.getEnabledActions(state)
    
    def onEnableAction(self, node, action):
        return self.strategy.onEnableAction(node, action)
    
    def chooseAction(self, state):
        if self.useDpor:
            return self.dpor.chooseAction(state)
        else:
            return self.strategy.chooseAction(state)

    def checkManageFaults(self, next_action, state):
        # These transitions will lower the budget available for fault injections
        if next_action.target in ["drop_packet", "duplicate_packet", "reorder_packet"]:
            state.model.decFaultInjectionCount()

    def _debugDumpStateStack(self):
        i = 0
        for s in self.state_stack:
            log.debug("%d -- %s" % (i, s))
            i += 1
        if len(self.state_stack) == 0:
            log.debug("State stack empty")

    def modelCheck(self):
        """ This method modifies the current state """
        backtrack = False
        path_end_cached_state = False
#       c = 0
        if MEMORY_PROFILING:
            objgraph.show_growth()
        while len(self.state_stack) > 0:
            log.warning("------> starting model checker transition (stack len: %d) <-------" % len(self.state_stack))
            start_state = self.state_stack.pop()
            self.state = start_state
            if not config.get("runtime.replay"):
                start_state.restoreState(self.strategy)
#           self._debugDumpStateStack()
            log.debug("Current:\n%s" % start_state)

            if MEMORY_PROFILING and self.good_transitions_count > 500:
                uo = gc.collect()
                log.debug("Garbage collector found %d unreachable objects" % uo)
                objgraph.show_growth()
                objgraph.show_most_common_types()
                # Use the code below to get a graph of the references to a
                # random object of a particular type. Install xdot for best results.
#               objgraph.show_chain(objgraph.find_backref_chain(
#                   random.choice(objgraph.by_type('EateController')),
#                   inspect.ismodule))
                utils.crash("memory testing")
            
#           c += 1
#           pprint(state_list, file("state_list%d.txt" % c, "w"), width=100)
#           print c

            # replay the list of actions if necessary
            if backtrack:
                log.info("Backtracking, previous path early termination: %s" % str(path_end_cached_state))
                path_end_cached_state = False

                pop = None
                if self.useDpor:
                    stats.pushProfile("dpor")
                    start_state.model = self.initial_state.model
                    start_state.invariant_dispatcher = self.initial_state.invariant_dispatcher
                    pop, start_state = self.dpor.startBacktracking(start_state)
                    stats.popProfile()              

                self.state = start_state

                if config.get("runtime.replay"):
                    replayed_state = self.replayActions(start_state)

                    # Sanity checks
                    if self.state_debug and replayed_state != start_state:
                        pprint(replayed_state, file("state_now.txt", "w"), width=100)
                        pprint(start_state, file("state_before.txt", "w"), width=100)
                        utils.crash("State after replay is different than original (debug enabled)")
                    start_state = replayed_state

                self.state = start_state

                if pop:
                    path_end_cached_state = True
                    if self.packetTranslator is not None:
                        self.packetTranslator.stopSniffing()
                    start_state.testPoint("path_end", cached_state=path_end_cached_state)
                    start_state.checkNewViolations() # clean the new_violation state
                    continue


            next_action = self.chooseAction(start_state)
            log.debug("Next action: " + str(next_action))

            # when dpor decided that the available enabled actions do not need to be executed
            if self.useDpor and next_action is None:
                backtrack = True
                path_end_cached_state = True
                if self.packetTranslator is not None:
                    self.packetTranslator.stopSniffing()
                start_state.testPoint("path_end", cached_state=path_end_cached_state)
                start_state.checkNewViolations() # clean the new_violation state
                continue

            if self.state_debug and backtrack:
                for a in self.getEnabledActions(start_state):
                    assert a in self.getEnabledActions(start_state) or a.node_name == "model_checker"

            if self.graph != None:
                self.graph.startTransition(start_state)

            # Performing the transition would make us to go over the cutoff limit, backtrack
            if config.get("model.cutoff") > 0 and start_state.path_length+1 > config.get("model.cutoff"):
                log.warning("Path cutoff limit reached")
                path_end_cached_state = True
                backtrack = True
                if self.packetTranslator is not None:
                    self.packetTranslator.stopSniffing()
                start_state.testPoint("path_end", cached_state=path_end_cached_state)
                start_state.checkNewViolations() # clean the new_violation state
                continue

            # make a copy of the model before modifying it
            new_state = None
            if not config.get("runtime.replay") or self.state_debug:
                new_state = start_state.copy()
                new_state.restoreState()
            else:
                new_state = start_state
                start_state = new_state.minimal_copy()

            if self.state_debug:
                new_state.state_replay_list += [start_state]

            self.state = new_state

            # add the current state back to the stack, if there is still something to explore
            if start_state.hasAvailableActions():
                if not config.get("runtime.replay") or self.state_debug:
                    start_state.storeState(self.strategy)
                self.state_stack.append(start_state)

            if next_action.target == "port_stats_special":
                self.portStatsSpecial(new_state, next_action.args[0])

            self.checkManageFaults(next_action, new_state)

            new_state.testPoint("transition_start")

            ### Execute the transition ###
            new_state.executeAction(next_action, start_state.path_length+1)

            if self.graph != None:
                self.graph.endTransition(new_state, str(next_action))

            new_state.testPoint("transition_end")
            if new_state.checkNewViolations(): # Check if we need to go on or backtrack
                log.info("Invariant violations reported, path exploration stopped")
                path_end_cached_state = True
                backtrack = True
                if self.packetTranslator is not None:
                    self.packetTranslator.stopSniffing()
                new_state.testPoint("path_end", cached_state=path_end_cached_state)
                new_state.checkNewViolations() # clean the new_violation state
                continue

            if self.max_path_length < new_state.path_length:
                self.max_path_length = new_state.path_length

            self.good_transitions_count += 1

            # It we reached a new state, hash it and put on top of the stack
            new_state.setAvailableActions(self.getEnabledActions(new_state))
            state_hash = hash(new_state)
            if not state_hash in self.unique_states:
                self.unique_states.add(state_hash)
                if new_state.hasAvailableActions():
                    if not config.get("runtime.replay") or self.state_debug:
                        new_state.storeState(self.strategy)
                    self.state_stack.append(new_state)
                    backtrack = False
                    log.debug("New state with ID: %d" % new_state.state_id)
                else:
                    log.info("No more actions available, end state reached.")
                    backtrack = True
                    if self.packetTranslator is not None:
                        self.packetTranslator.stopSniffing()
                    new_state.testPoint("path_end", cached_state=path_end_cached_state)
                    new_state.checkNewViolations() # clean the new_violation state
            else:
                log.info("Reached a known state, stopping path exploration")
                path_end_cached_state = True
                self.old_states_count += 1
                backtrack = True
                if self.packetTranslator is not None:
                    self.packetTranslator.stopSniffing()
                new_state.testPoint("path_end", cached_state=path_end_cached_state)
                new_state.checkNewViolations() # clean the new_violation state

        new_state.testPoint("path_end", cached_state=path_end_cached_state)
        new_state.checkNewViolations() # clean the new_violation state

        if self.packetTranslator is not None:
            self.packetTranslator.destroyTopo()

    def printStats(self, sig, frame):
        total_per_sec = self.good_transitions_count - self.total_last_sec
        sys.stdout.write("Total: %d, uniq: %d, revis: %d, max path len: %d, viols: %s, SE calls: %d, stack len: %d (%d tr/sec)\r" % \
                    (self.good_transitions_count, len(self.unique_states), self.old_states_count, self.max_path_length, sum([x[0] for x in self.violation_counter.values()]), self.sym_engine_call_count, len(self.state_stack), total_per_sec))
        sys.stdout.flush()
        self.total_last_sec = self.good_transitions_count

    def gotoInitialState(self):
        """ This method modifies the current state """
        if self.initial_state is None:
            model = self.model_class()
            model.initTopology(None)
            model.setFaultInjectionCount(config.get("model.faults"))
        else:
            self.initial_state.restoreState(self.strategy)
            state = self.initial_state.copy(get_app_state=True) # nel component prende lo stato attuale dal modulo! maledizione...
            state.restoreState(self.strategy)
            model = state.model

        if self.packetTranslator is None and config.get("model.use_real_switch"):
            from real_switch.packet_translator import PacketTranslator
            self.packetTranslator = PacketTranslator(model)

        if self.packetTranslator is not None:
            self.packetTranslator.restartTopo()

        random.seed("NSL")

        if self.initial_state is None:
            model.start(self)

        self.strategy.visitModel(model)
        if self.useDpor:
            self.dpor.updateDependencies(model)
            for node in model.getNodes():
                node.communicationObjectUsed = self.dpor.communicationObjectUsed
                node.startActionExecution = self.dpor.startActionExecution
                node.finishActionExecution = self.dpor.finishActionExecution

        if self.initial_state is None:
            inv_dis = InvariantDispatcher(self)
            for i in model.invariants:
                inv_dis.registerInvariant(i)
            state = ModelCheckerState(model, inv_dis)
            state.storeState(self.strategy)
            state.restoreState()
            self.violation_counter = state.invariant_dispatcher.violation_counter
            state.setAvailableActions(self.getEnabledActions(state))
            self.initial_state = state.copy()
            self.initial_state.storeState(self.strategy)

        state.testPoint("path_start")
        return state

    def replayActions(self, target_state):
        """ This method modifies the current state """
        log.info("Start replay, length: %d" % target_state.path_length)
        stats.pushProfile("replay actions")

        state = self.gotoInitialState()
        self.state = state
        d = 1
        for a in target_state.replay_list:
            log.debug(state)
            if self.useDpor:
                self.dpor.replayAction(a)

            if a.target == "port_stats_special":
                self.portStatsSpecial(state, a.args[0])

            if not a in state.getAllEnabledActions():
                state.model.printEnabledActions()
                utils.crash("Action %s not available during replay" % a)

            self.checkManageFaults(a, state)            
            self.strategy.beforeReplayAction(a)
            state.executeAction(a, d, is_replaying=True)
            state.setAvailableActions(self.getEnabledActions(state))

            if self.state_debug and d < target_state.path_length:
                expected_state = target_state.state_replay_list[d]
                if state != expected_state:
                    pprint(target_state.state_replay_list, file("state_list.txt", "w"), width=100)
                    utils.crash("State at step %d during replay is different than original" % d)
                else:
                    log.debug("Replay state: ok")

            d += 1
        state.replay_list = target_state.replay_list
        state.state_replay_list = target_state.state_replay_list
        state.available_actions = target_state.available_actions
        stats.popProfile()
        log.info("End replay")
        return state

    def portStatsSpecial(self, state, dp_id):
        cnt_state = state.model.getControllerAppState()
        ser_state = cPickle.dumps((dp_id, cnt_state), -1)
        if ser_state not in self.contr_app_states_stats:
            self.contr_app_states_stats[ser_state] = self.generatePortStats(ser_state)
        else:
            #print "stats from cache"
            pass

        inputs = self.contr_app_states_stats[ser_state]
        assert len(inputs) > 0
        for inp in inputs:
            a = Action("ctrl", "port_stats", (dp_id, inp["ports"]))
            state.model.controller.enableAction("port_stats", (dp_id, inp["ports"]))


class DebugModelChecker(ModelChecker):
    def __init__(self, symbolic_options):
        ModelChecker.__init__(self, symbolic_options)
        self.action_list = []
        self.action_cache = []

    def chooseAction(self, state):
        print "Actions taken:"
        print self.action_list
        print "Choose next action:"
        for i, e in enumerate(state.available_actions):
            print i, "--", e
            if e.target == "process_command":
                print "CMD:", state.model.nodes[e.node_name].command_queue[0]
            elif e.target == "process_packet":
                for p in state.model.nodes[e.node_name].ports.values():
                    if len(p.in_buffer) > 0:
                        print "PKT:", p.in_buffer[0]
        if self.action_cache == []:
            actions = sys.stdin.readline().strip()
            for action in actions.split(","):
                action_id = int(action.strip())
                self.action_cache.append(action_id)
        assert len(self.action_cache) > 0

        action_id = self.action_cache.pop(0)
        self.action_list.append(action_id)
        return state.available_actions.pop(action_id)

