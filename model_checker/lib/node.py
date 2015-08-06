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

from lib.port import Port
from lib.action import Action
from nox.lib import openflow

import logging
import abc, copy
import utils

class Node:
    __metaclass__ = abc.ABCMeta

    def __init__(self, name, port_count):       
        self.name = name
        self.log = logging.getLogger("nice.mc.%s" % self.name)
        self.ports_object = {}
        port_name = 0
        while port_count > 0:
            self.ports[port_name] = Port(port_name)
            port_count -= 1
            port_name += 1

        self.enabled_actions = [] # Actions that the node can perform at the current state
        self.model_checker = None
        self.packet_counter = 0
        self.state = None
        
    @property
    def ports(self):
        self.communicationObjectUsed(self, "inputBuffer")
        return self.ports_object

    # methods replaced when DPOR is on
    def communicationObjectUsed(self, node, name, attrs = None):
        pass

    def startActionExecution(self, node, action):
        pass

    def finishActionExecution(self):
        pass


    def start(self, model_checker):
        self.model_checker = model_checker

    def enableAction(self, target, args=(), skip_dup=False):
        if not isinstance(args, tuple):
            args = (args,)
        action = Action(self.name, target, args)
        action = self.model_checker.onEnableAction(self, action)
        if skip_dup == True and action in self.enabled_actions:
            return False
        self.log.debug("New enabled action: %s" % str(action))
        self.enabled_actions.append(action)
        self.log.debug("Enabled actions for '%s': %s" % (self.name, self.enabled_actions))
        return True

    def runAction(self, action):
        assert action in self.enabled_actions
        if not hasattr(self, action.target):
            raise NotImplementedError(action.target)

        cb = getattr(self, action.target)

        self.startActionExecution(self, action)

        ret = cb(*action.args)
        if ret == None:
            self.finishActionExecution()
            utils.crash("action did not return valid value!")
#       self.log.debug("Node %s Enabled actions: %s" % (self.name,self.enabled_actions))
        if ret == True:
            self.enabled_actions.remove(action)
#       self.log.debug("Node %s Enabled actions: %s" % (self.name,self.enabled_actions))
        self.finishActionExecution()

    def removeAction(self, target):
        self.enabled_actions = [action for action in self.enabled_actions if action.target != target]

    def countPorts(self):
        return len(self.ports)

    def movePeer(self, port_from, port_to):
        self.ports[port_to].peer = self.ports[port_from].peer
        self.ports[port_to].peer_port = self.ports[port_from].peer_port
        self.ports[port_from].peer = None
        self.ports[port_from].peer_port = None

    def getPeer(self, port_name):
        try:
            return self.ports[port_name].peer
        except:
            utils.crash("Wrong topology: %s has no port named %s" % (self.name, port_name))

    def getPeerPort(self, port_name):
        return self.ports[port_name].peer_port
    
    def getWaitingPacket(self, port_name):
        port = self.ports[port_name]
        if len(port.in_buffer) > 0:
            pkt = port.in_buffer.pop(0)
            self.state.testPoint("packet_received", receiver=self, packet=pkt, port=port)
            return pkt
        else:
            return None

    def checkWaitingPacket(self, port_name):
        if len(self.ports[port_name].in_buffer) > 0:
            return True
        else:
            return False

    def initTopology(self, port_setup):
        for port in port_setup:
            self.ports[port].peer = port_setup[port][0]
            self.ports[port].peer_port = port_setup[port][1]
            self.ports[port].of_status = 0

    def enqueuePacket(self, packet, inport):
        if self.ports[inport].of_status & openflow.OFPPS_LINK_DOWN:
            return # Drop packet
        try:
            self.ports[inport].queueIn(packet)
        except KeyError:
            utils.crash("Wrong topology: %s has no port named %s" % (self.name, inport))
        self.enableAction("process_packet", skip_dup=True)

    def process_packet(self):
        raise NotImplementedError

    def genPacketID(self):
        pktid = self.name + str(self.packet_counter)
        self.packet_counter += 1
        return pktid

    def sendPacket(self, packet, port):
        packet = packet.copy()
        peer = self.getPeer(port)
        peer.enqueuePacket(packet, self.getPeerPort(port))
        self.state.testPoint("packet_sent", sender=self, receiver=peer, packet=packet)

    def signalPortDown(self, port_no):
        pass

    def __repr__(self):
    #   return str((self.name, self.enabled_actions, self.ports))
        return self.name

    @abc.abstractmethod
    def dump_equivalent_state(self):
        filtered_dict = {}
        filtered_dict["enabled_actions"] = utils.copy_state(self.enabled_actions)
        filtered_dict["ports"] = utils.serialize_dict(self.ports)
        return filtered_dict

    def __deepcopy__(self, memo):
        c = type(self).__new__(type(self))
        memo[id(self)] = c
        d = c.__dict__
        for k in self.__dict__:
            if k == "log":
                d[k] = self.log
                continue
            elif k == "state":
                d[k] = None
                continue
            elif k == "model_checker":
                d[k] = self.model_checker
                continue
            elif k == "communicationObjectUsed":
                d[k] = self.communicationObjectUsed
                continue
            elif k == "startActionExecution":
                d[k] = self.startActionExecution
                continue
            elif k == "finishActionExecution":
                d[k] = self.finishActionExecution
                continue
            elif k == "mod":
                d[k] = self.mod
                continue
            try:
                d[k] = copy.deepcopy(self.__dict__[k], memo)
            except RuntimeError:
                utils.crash(k)

        return c
