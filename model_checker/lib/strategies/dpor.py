#
# Copyright (c) 2011, EPFL (Ecole Politechnique Federale de Lausanne)
# All rights reserved.
#
# Created by Marco Canini, Daniele Venzano, Dejan Kostic, Jennifer Rexford
# Contribued to this file: Maciej Kuzniar
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

from lib.strategies.strategy import Strategy

import nox.lib.core as core
from stats import getStats
stats = getStats()

class TreeNode:
    def __init__(self, value = None):
        self.parentNode = None
        self.children = []
        self.nothingToDo = False
        self.value = value
        self.enabledActions = []
        self.initialEnabledActions = []
        self.addedActions = []
        self.enabledActionsInitialized = False
        self.stronglyEnabledActions = []
        self.actionsToDelete = []
        self.blockedActions = {}
        self.visitedActions = []

    def __repr__(self):
        return str((self.value, self.nothingToDo))

    def addChild(self, child):
        self.children.append(child)
        child.parentNode = self


class Tree:
    def __init__(self):
        self.root = TreeNode()
        self.currentNode = self.root

    def addNode(self, action):
        newNode = TreeNode(action)
        self.currentNode.addChild(newNode)
        return newNode

    def getChild(self, node, action):
        children = filter(lambda x: x.value == action, node.children)
        assert len(children) < 2 
        if len(children) > 0:
            return children[0]
        return None

    def goToRoot(self):
        self.currentNode = self.root

    def followAction(self, action):
        child = self.getChild(self.currentNode, action)
        assert child is not None
        self.currentNode = child
        return child.value
        

class DynamicPartialOrderReduction(Strategy):   

    def __init__(self, model_checker, strategy):
        Strategy.__init__(self, model_checker)
        self.strategy = strategy
        self.tree = Tree()
        self.currentPath = []
        self.lastPath = []
        self.lastBranchingPoint = 0
        self.lastBranchingNode = self.tree.root
        self.pathTheSame = True
        self.dependent = {}
        self.flowTableReads = {}
        self.flowTableWrites = {}
        self.flowAttributes = {}
        self.recalculationRequired = False
        self.before = []
        self.actionExecuted = None
        self.distinctiveAttrs = [core.IN_PORT, core.DL_SRC, core.DL_DST, core.DL_TYPE, core.NW_PROTO, core.NW_TOS, core.TP_SRC, core.TP_DST]

    def startBacktracking(self, state):
        """Runs the whole DPOR procedure when exploration reaches the state where backtracking is required (no more enabled actions, state already visited, invariant violation)
        """
        self.finishActionExecution()
        if not self.recalculationRequired:
            self.reset()
            return None, state

#       self.printDependencies()

        self.recalculateHappensBefore()
        self.doDpor(state)
        pop, new_state = self.clearStack(state)
        
        self.reset()
        return pop, new_state


    def recalculateHappensBefore(self):
        """Updates the happens before based on added actions in each node.
        """
        tempCurrentNode = self.lastBranchingNode
            
        self.before = self.before[:self.lastBranchingPoint]
        i = self.lastBranchingPoint
        for action1 in self.currentPath[self.lastBranchingPoint:]:
            j = i - 1
            tempCurrentNode2 = tempCurrentNode
            while j >= 0 and self.currentPath[i] not in tempCurrentNode2.addedActions:
                tempCurrentNode2 = tempCurrentNode2.parentNode
                j -= 1
            if j >= 0:
                self.before.append(self.before[j] + [j])
            else:
                self.before.append([])
            i += 1
            tempCurrentNode = self.tree.getChild(tempCurrentNode, action1)
    
    def reset(self):
        self.tree.goToRoot()
        self.lastPath = self.currentPath[:]
        self.currentPath = []
        self.lastBranchingPoint = 0
        self.lastBranchingNode = self.tree.root
        self.pathTheSame = True     
        self.recalculationRequired = False

    def doDpor(self, state):
        """Check which actions on the current path should be reordered and adds appropriate branches in the tree. 
        """
        i = 0
        tempCurrentNode = self.tree.root
        for action1 in self.currentPath[0:len(self.currentPath) - 1]:
            j = max(i + 1, self.lastBranchingPoint)
            for action2 in self.currentPath[j:len(self.currentPath)]:
                if len(filter(lambda action: action not in tempCurrentNode.stronglyEnabledActions, tempCurrentNode.enabledActions)) == 0:
                    break
                stats.pushProfile("ifdep")
                if (i not in self.before[j] and self.actionsDependent(state, action1, action2, i, j)):
                    bef  = filter(lambda x : x > i, self.before[j])
                    if len(bef) > 0:
                        # there is an action that has to be run before action2. Force order action2 -> action1 in this branch
                        child = self.tree.getChild(tempCurrentNode, self.currentPath[bef[0]])
                        if child is not None:
                            if action1 not in child.blockedActions.keys():
                                child.blockedActions[action1] = [action2]
                                child.visitedActions.extend(filter(lambda action: action not in child.visitedActions, self.currentPath[i:j+1]))
                            elif action2 not in child.blockedActions[action1]:
                                child.blockedActions[action1].append(action2)
                                child.visitedActions.extend(filter(lambda action: action not in child.visitedActions, self.currentPath[i:j+1]))
                        elif self.currentPath[bef[0]] not in tempCurrentNode.stronglyEnabledActions and self.currentPath[bef[0]] in tempCurrentNode.enabledActions:
                            tempCurrentNode.stronglyEnabledActions.append(self.currentPath[bef[0]])
                            newNode = TreeNode(self.currentPath[bef[0]])
                            newNode.blockedActions[action1] = [action2]
                            newNode.visitedActions.extend(self.currentPath[i:j+1])
                            tempCurrentNode.addChild(newNode)
                    elif action2 not in tempCurrentNode.stronglyEnabledActions:
                        tempCurrentNode.stronglyEnabledActions.append(action2)
                stats.popProfile()  
                j+=1
                
            i+=1
            #Actions that appeared on the current path. If they are not explicitly marked as necessary to execute (strongly enabled) in tempCurrentNode, they will be ignored when processing returns to tempCurrentNode
            tempCurrentNode.actionsToDelete.extend(filter(lambda action: action not in tempCurrentNode.actionsToDelete and action in self.currentPath[max(i, self.lastBranchingPoint - 1):], tempCurrentNode.enabledActions))
            tempCurrentNode = self.tree.getChild(tempCurrentNode, action1)

    def clearStack(self, state):
        """Removes unnecessary states from the model checker stack. If there are no enabled actions in the state (as a result of DPOR working), it is not necessary to check this state again.
        """
        if len(self.tree.currentNode.enabledActions) == 0:
            self.tree.currentNode.nothingToDo = True    
            
        pop = False
        while not pop and self.tree.currentNode != self.tree.root and len(self.tree.currentNode.enabledActions) == 0:
            if self.currentPath == state.replay_list:
                if len(self.model_checker.state_stack) > 0:
                    state = self.model_checker.state_stack[-1]
                pop = True
            self.goBackOneLevel()
        
        while pop and self.tree.currentNode != self.tree.root and len(self.tree.currentNode.enabledActions) == 0 and len(self.model_checker.state_stack) > 1:
            if self.currentPath == state.replay_list:
                self.model_checker.state_stack.pop()
                state = self.model_checker.state_stack[-1]
            self.goBackOneLevel()

        return pop, state
    
    def goBackOneLevel(self):
        self.currentPath.pop()
        self.tree.currentNode.children = []
        self.tree.currentNode = self.tree.currentNode.parentNode
        self.tree.currentNode.enabledActions = filter(lambda action: action in self.tree.currentNode.stronglyEnabledActions or action not in self.tree.currentNode.actionsToDelete, self.tree.currentNode.enabledActions)


    def replayAction(self, action):
        """Keeps dpor tree and current path synchronized with model checker when the actions are replayed to reach the required state.
           Optimization as happens before and dpor does not have to be recalculated for part of the path that was the same for the previous state.
        """
        actionFollowed = self.tree.followAction(action)
        self.currentPath.append(actionFollowed)
        if self.pathTheSame and self.lastBranchingPoint < len(self.lastPath) and self.currentPath[self.lastBranchingPoint] == self.lastPath[self.lastBranchingPoint]:
            self.lastBranchingPoint += 1
            self.lastBranchingNode = self.tree.getChild(self.lastBranchingNode, action)
        else:
            self.pathTheSame = False
            

    def chooseAction(self, state):
        """Updates the DPOR tree and returns the next action to be executed based on the strategy and current state. Return None when no action is available
        """
        action = None
        if not self.tree.currentNode.enabledActionsInitialized:
            #Initialize the node with all possible actions. 
            #Compute actions that where added in this node but where not present in the parent node.    
            #Compute actions that where removed from enabled actions but not as a result of action execution (heuristics).
            self.tree.currentNode.enabledActions = state.available_actions[:]
            self.tree.currentNode.initialEnabledActions = state.available_actions[:]
            if self.tree.currentNode != self.tree.root:
                self.tree.currentNode.disappearingActions = filter(lambda action: action not in self.tree.currentNode.initialEnabledActions, self.tree.currentNode.parentNode.disappearingActions)
                self.tree.currentNode.disappearingActions += filter(lambda action: self.tree.currentNode != self.tree.root and action != self.tree.currentNode.value and action not in self.tree.currentNode.initialEnabledActions, self.tree.currentNode.parentNode.initialEnabledActions)
            else:
                self.tree.currentNode.disappearingActions = []

            self.tree.currentNode.addedActions = filter(lambda action: self.tree.currentNode == self.tree.root or action == self.tree.currentNode.value or (action not in self.tree.currentNode.parentNode.initialEnabledActions and action not in self.tree.currentNode.parentNode.disappearingActions), self.tree.currentNode.initialEnabledActions)
            self.tree.currentNode.enabledActionsInitialized = True
            
        
        if len(self.tree.currentNode.children) > 0:
            assert len(filter(lambda action: action not in state.available_actions, self.tree.currentNode.enabledActions)) == 0

            if len(self.tree.currentNode.enabledActions) == 0:
                self.tree.currentNode.nothingToDo = True
                del state.available_actions[:]
                return None

        #enabled_actions = self.tree.currentNode.enabledActions[:]
        #find action that is enabled and is not blocked by forcing actions order in the current branch
        while len(self.tree.currentNode.enabledActions) > 0:
            #TODO: ugly, but strategy now uses state instead of a list of actions
            #old version was action = self.tree.currentNode.enabledActions.pop(0)
            tmp = state.available_actions[:]
            state.setAvailableActions(self.tree.currentNode.enabledActions)
            action = self.strategy.chooseAction(state)
            state.setAvailableActions(tmp)
            if action not in self.tree.currentNode.blockedActions.keys():
                break
            action = None

        del state.available_actions[:]
        state.available_actions.extend(self.tree.currentNode.enabledActions)

        if len(state.available_actions) == 0 and action is None:
            self.tree.currentNode.nothingToDo = True
            return None

        self.recalculationRequired = True

        if len(self.tree.currentNode.children) > 0:
            tempCurrentNode = self.tree.getChild(self.tree.currentNode, action)
            if tempCurrentNode is not None:
                self.tree.currentNode = tempCurrentNode
                self.currentPath.append(self.tree.currentNode.value)
                return action


        self.currentPath.append(action)
        newNode = self.tree.addNode(action)
        # unblock actions blocked by forcing order in the branch when the previous action has been chosen or an unexplored action appeared
        if action in self.tree.currentNode.visitedActions:
            for key in self.tree.currentNode.blockedActions.keys():
                if action not in self.tree.currentNode.blockedActions[key]:
                    newNode.blockedActions[key] = self.tree.currentNode.blockedActions[key][:]
            newNode.visitedActions.extend(self.tree.currentNode.visitedActions)
        self.tree.currentNode = newNode

        return action

    def updateDependencies(self, model):
        self.dependent = {}
        self.flowTableReads = {}
        self.flowTableWrites = {}
        return

    def communicationObjectUsed(self, node, name, attrs = None):
        """Updates dictionaries of dependency on communication object if the object was used during action execution. This method is executed by the nodes.
           The communication objects are: controller.component, node.buffer, switch.flowTable.
           Flow Table reads and writes are treated separately and with additional optimization when the records might be consider as independent (actionsDependentWriteWrite, actionsDependentReadWrite)
        """
        if self.actionExecuted is None:
            return

        assert self.actionExecuted == self.currentPath[len(self.currentPath)-1]

        if name == "flowTable_read":
            if node.name not in self.flowTableReads.keys():
                self.flowTableReads[node.name] = [(self.actionExecuted, len(self.currentPath) - 1)]
            elif (self.actionExecuted, len(self.currentPath) - 1) not in self.flowTableReads[node.name]:
                self.flowTableReads[node.name].append((self.actionExecuted, len(self.currentPath) - 1))
            self.flowAttributes[len(self.currentPath) - 1] = attrs
            return

        if name == "flowTable_write":
            if node.name not in self.flowTableWrites.keys():
                self.flowTableWrites[node.name] = [(self.actionExecuted, len(self.currentPath) - 1)]
            elif (self.actionExecuted, len(self.currentPath) - 1) not in self.flowTableWrites[node.name]:
                self.flowTableWrites[node.name].append((self.actionExecuted, len(self.currentPath) - 1))
            self.flowAttributes[len(self.currentPath) - 1] = attrs
            return

        name = node.name + "." + name
        if name not in self.dependent.keys():
            self.dependent[name] = [(self.actionExecuted, len(self.currentPath) - 1)]
        elif (self.actionExecuted, len(self.currentPath) - 1) not in self.dependent[name]:
            self.dependent[name].append((self.actionExecuted, len(self.currentPath) - 1))


    def startActionExecution(self, node, action):
        assert self.actionExecuted is None
        self.actionExecuted = action

    def finishActionExecution(self):
        self.actionExecuted = None


    def actionsDependent(self, state, action1, action2, pos1, pos2):
        """Checks if 2 actions on the current path are dependent.
        """
        if action1 == action2:
            return False
        # discover_packets should be run whenever possible, so it is always dependent
        if action1.target == "discover_packets" or action2.target == "discover_packets":
            return True
        # move host may affect any other action
        if action1.target == "move_host_" or action2.target == "move_host_":
            return True
        
        # discover_packets will not be called if all packets have been sent. It is necessary to switch all possible actions with sending packet by a "symbolic" node.
        # Possible optimization: actions changing controller state only
        if action1.target == "send_packet":
            node = state.model.nodes[action1.node_name]
            if hasattr(node, "discover_packets"):
                return True
        if action2.target == "send_packet":
            node = state.model.nodes[action2.node_name]
            if hasattr(node, "discover_packets"):
                return True

        # standard dependency - using the same communication object, except for the flow table
        for key in self.dependent.keys():
            if (action1, pos1) in self.dependent[key] and (action2, pos2) in self.dependent[key]:
                return True
        
        # dependency based on the flow table
        for key in self.flowTableWrites.keys():
            if (action1, pos1) in self.flowTableWrites[key] and (action2, pos2) in self.flowTableWrites[key]:
                return self.actionsDependentWriteWrite(self.flowAttributes[pos1], self.flowAttributes[pos2])
            if key in self.flowTableReads.keys():
                if (action1, pos1) in self.flowTableWrites[key] and (action2, pos2) in self.flowTableReads[key]:
                    return self.actionsDependentReadWrite(self.flowAttributes[pos2], self.flowAttributes[pos1])
                if (action1, pos1) in self.flowTableReads[key] and (action2, pos2) in self.flowTableWrites[key]:
                    return self.actionsDependentReadWrite(self.flowAttributes[pos1], self.flowAttributes[pos2])
                
        return False

    

    def actionsDependentWriteWrite(self, attrs1, attrs2):
        """Checks if flow table updates are dependent. If it is impossible that packet matches both rules, they are independent.
        """
        for attr in self.distinctiveAttrs:
            if attr in attrs1.keys() and attr in attrs2.keys() and attrs1[attr] != attrs2[attr]:
                return False
        
        for address in [(core.NW_SRC, core.NW_SRC_N_WILD), (core.NW_DST, core.NW_DST_N_WILD)]:
            ip, mask = address
            if ip in attrs1.keys() and ip in attrs2.keys():
                mask1 = attrs1[mask] if mask in attrs1.keys() else 0
                mask2 = attrs2[mask] if mask in attrs2.keys() else 0
                min_mask = int(0xffffffff << max(mask1, mask2))
                if attrs1[ip] & min_mask != attrs2[ip] & min_mask:
                    return False
        
        return True

    def actionsDependentReadWrite(self, attrs1, attrs2):
        """Checks if flow table update and match checking are dependent. If it is impossible that packet matching check is affected by updated rule, the actions are indepondent.
        """
        for attr in self.distinctiveAttrs:
            if attr in attrs2.keys():
                if (attr not in attrs1.keys()) or (attr in attrs1.keys() and attrs1[attr] != attrs2[attr]):
                    return False
        
        for address in [(core.NW_SRC, core.NW_SRC_N_WILD), (core.NW_DST, core.NW_DST_N_WILD)]:
            ip, mask = address
            if ip in attrs2.keys():
                if ip not in attrs1.keys():
                    return False
                
                mask1 = attrs1[mask] if mask in attrs1.keys() else 0
                mask2 = attrs2[mask] if mask in attrs2.keys() else 0
                min_mask = int(0xffffffff << max(mask1, mask2))
                if attrs1[ip] & min_mask != attrs2[ip] & min_mask:
                    return False
        
        return True

    def printDependencies(self):
        for key in self.dependent.keys():
            print key, ":", self.dependent[key]

        print "WRITES"
        for key in self.flowTableWrites.keys():
            print key, ":", self.flowTableWrites[key]

        print "READS"
        for key in self.flowTableReads.keys():
            print key, ":", self.flowTableReads[key]

