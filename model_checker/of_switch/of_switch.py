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

from lib.node import Node
from invariants.violation import Violation

import nox.lib.openflow as openflow
import nox.lib.core as core
import nox.lib.util as of_util
from nox.lib.packet.mac_address import MacAddress
from nox.lib.packet.ip_address import IpAddress
from nox.lib.packet.ethernet import ethernet

from lib.of_packet_out_message import PacketOutMessage
from lib.of_flow_table_modification_message import FlowTableModificationMessage
from lib.of_port_status_message import PortStatusMessage

import logging
import utils

class FlowTableEntry:
    def __init__(self, attrs, actions, priority, send_flow_rem=False):
        self.attrs = attrs
        self.actions = actions
        self.priority = priority
        self.send_flow_rem = send_flow_rem

    def __lt__(self, other):
        my_attrs = utils.flatten_dict(self.attrs)
        other_attrs = utils.flatten_dict(other.attrs)
        if my_attrs != other_attrs:
            return my_attrs < other_attrs
        else:
            return self.actions < other.actions

    def __eq__(self, other):
        eq = True
        eq = eq and self.attrs == other.attrs
        eq = eq and self.actions == other.actions
        eq = eq and self.priority == other.priority
        eq = eq and self.send_flow_rem == other.send_flow_rem
        return eq

    def __ne__(self, other):
        return not self.__eq__(other)

    def dump_equivalent_state(self):
        filtered_dict = {}
        filtered_dict["actions"] = utils.copy_state(self.actions)

        filtered_dict["attrs"] = utils.copy_state(self.attrs)

        filtered_dict["priority"] = utils.copy_state(self.priority)
        filtered_dict["send_flow_rem"] = utils.copy_state(self.send_flow_rem)

        return filtered_dict

    def __repr__(self):
        return str((self.attrs, self.actions, self.priority))

class OpenflowSwitch(Node):
    ALWAYS_NEW_STATE = False

    def __init__(self, name, port_count, of_id, expire_entries=False):
        Node.__init__(self, name, port_count)
        self.log = logging.getLogger("nice.mc.%s" % self.name)
        self.flow_table_object = []
        self.openflow_id = of_id
        self.buffers = []
        self.next_buffer_id = 0
        self.packet_store = {}
        self.command_queue = []
        self.fault_injection_count = 0
        self.state_cnt = 0
        self.expire_entries = expire_entries
        self.ports_to_fail = []
        self.this_switch_is_offline = False

    def start(self, model_checker):
        Node.start(self, model_checker)
        for p in self.ports_to_fail:
            self.enableAction("link_fault_down", p)

    @property
    def flow_table(self):
#       self.communicationObjectUsed(self, self.name + ".flowTable")
        return self.flow_table_object

    def __repr__(self):
        return "%s (id: %d)" % (self.name, self.openflow_id)

    def getOpenflowID(self):
        return self.openflow_id

    def setFaultInjectionCount(self, count):
        """ this gets called after initTopology and when a fault action is executed """
        self.fault_injection_count = count

    # NOTE: function overloaded from Node.
    def enqueuePacket(self, packet, inport):
        self.create_new_state()
        if self.ports[inport].of_status & openflow.OFPPS_LINK_DOWN:
            return # Drop packet
        if self.this_switch_is_offline:
            return # Drop packet

        self.log.debug("Queued packet %s on port %d" % (packet, inport))
        self.ports[inport].queueIn(packet)
        self.enableAction("process_packet", skip_dup=True)
        if self.fault_injection_count > 0:
#           self.enableAction("drop_packet", args=(inport,), skip_dup=True)
            self.enableAction("duplicate_packet", args=(inport,), skip_dup=True)
#           self.enableAction("reorder_packet", args=(inport,), skip_dup=True)

    def drop_packet(self, inport):
        """ Dequeues the first packet from the specified port and throws it away """
        self.create_new_state()
        more_packets = False
        pkt = self.getWaitingPacket(inport)
        if pkt != None and self.checkWaitingPacket(inport):
            more_packets = True

        return not (more_packets and self.fault_injection_count > 0)

    def duplicate_packet(self, inport):
        """ Creates a copy of the the first packet on the port and puts it on the end of the buffer """
        self.create_new_state()
        pkt = self.getWaitingPacket(inport)
        if pkt == None:
            self.log.debug("Empty buffer, no packets duplicated")
            return True

        self.ports[inport].in_buffer.insert(0, pkt)
        pkt2 = pkt.copy()
        pkt.fault_injection.append("HAS DUP")
        pkt2.fault_injection.append("DUP")
        self.ports[inport].in_buffer.append(pkt2)
        self.log.debug("Duplicated packet on port %d: %s" % (inport, pkt))

        return not self.fault_injection_count > 0

    def setPortsCanFail(self, port_list):
        self.ports_to_fail = port_list[:]

    def link_fault_down(self, port):
        self.create_new_state()
        if self.ports[port].of_status & openflow.OFPPS_LINK_DOWN:
            return
        self.ports[port].of_status |= openflow.OFPPS_LINK_DOWN
        self.ports[port].peer.ports[self.ports[port].peer_port].of_status |= openflow.OFPPS_LINK_DOWN
        self.signalPortDown(port)
        self.ports[port].peer.signalPortDown(self.ports[port].peer_port)
        return True
    
    def signalPortDown(self, port_no):
        self.log.error("Port down: %d, %d, %d" % (self.openflow_id, port_no, self.ports[port_no].of_status))
        ps = PortStatusMessage()
        ps.port_no = port_no
        ps.state = self.ports[port_no].of_status
        self.state.model.controller.enableAction("port_status", (self.openflow_id, openflow.OFPPR_MODIFY, ps))

    def enableFailure(self):
        self.create_new_state()
        self.enableAction("switch_fault_down", (self.openflow_id,))

    def switch_fault_down(self, dp_id):
        self.create_new_state()
        self.this_switch_is_offline = True
        self.enabled_actions = []
        for p in self.ports:
            if self.ports[p].peer != None:
                self.ports[p].peer.signalPortDown(self.ports[p].peer_port)
        self.state.model_checker.model.switch_failures_count -= 1
        if self.state.model_checker.model.switch_failures_count <= 0:
            for s in self.state.model_checker.model.switches:
                s.removeAction("switch_fault_down")
        return True

    def reorder_packet(self, inport):
        """ Appends the first packet at the end of the buffer """
        self.create_new_state()
        pkt = self.getWaitingPacket(inport)
        if pkt == None:
            return True

        pkt.fault_injection.append("REORD")
        self.ports[inport].in_buffer.append(pkt)

        return not self.fault_injection_count > 0

    def processActions(self, packet, actions, inport):
        """Process a set of actions on the packet"""
        for action in actions:
            if action[0] == openflow.OFPAT_OUTPUT:
                port = action[1][1]
                if port < openflow.OFPP_MAX:
                    peer = self.getPeer(port)
                    if peer == None:
                        continue # Skip disconnected port
                    self.enqueuePacketToNode(peer, packet.copy(), self.getPeerPort(port))
                    self.state.testPoint("switch_sent_packet_on_port", switch=self, packet=packet, port=port)
                elif port == openflow.OFPP_FLOOD:
                    self.state.testPoint("switch_flood_packet_start", switch=self, packet=packet)
                    for port in self.ports:
                        if port == inport:
                            continue # Skip the inport
                        peer = self.getPeer(port)
                        if peer == None:
                            continue # Skip disconnected port
                        self.enqueuePacketToNode(peer, packet.copy(), self.getPeerPort(port))
                        self.state.testPoint("switch_sent_packet_on_port", switch=self, packet=packet, port=port)
                elif port == openflow.OFPP_CONTROLLER:
                    self.sendQueryToController(packet, inport, openflow.OFPR_ACTION, action[1][0])
                elif port == openflow.OFPP_IN_PORT:
                    peer = self.getPeer(inport)
                    if peer == None:
                        continue
                    self.enqueuePacketToNode(peer, packet.copy(), self.getPeerPort(inport))
                    self.state.testPoint("switch_sent_packet_on_port", switch=self, packet=packet, port=inport)
                else:
                    utils.crash("Unknown port action: 0x%x" % port)

            elif action[0] == openflow.OFPAT_SET_DL_SRC: # Set Ethernet source address
                packet.src = MacAddress(action[1])
            elif action[0] == openflow.OFPAT_SET_NW_SRC: # Set IPv4 source address
                packet.next.srcip = IpAddress(action[1]) # We assume the next is an ipv4
            elif action[0] == openflow.OFPAT_SET_DL_DST: # Set Ethernet destination address
                packet.dst = MacAddress(action[1])
            elif action[0] == openflow.OFPAT_SET_NW_DST: # Set IPv4 source address
                packet.next.dstip = IpAddress(action[1]) # We assume the next is an ipv4
            else:
                utils.crash("Action not implemented: %x" % action[0])

    def packetIsMatching(self, pkt, inport, attrs):
        """Checks whether a packet is matching a specific table entry
        
           attrs is a dictionary of attributes to match, missing attributes
           are considered wildcarded
        """
        pkt_attrs = of_util.extract_flow(pkt)
        pkt_attrs[core.IN_PORT] = inport

        skip_nw_src = False
        for a in attrs:
            if a == "nw_src_n_wild":
                mask = int(0xffffffff << attrs[a]) # see openflow.h in NOX for this definition of mask
                if pkt_attrs[core.NW_SRC] & mask != attrs["nw_src"] & mask:
                    return False
                else:
                    skip_nw_src = True
            elif a == "nw_src" and skip_nw_src:
                continue
            elif attrs[a] != pkt_attrs[a]: # If this throws an exception, we have an usupported attribute
                return False
        return True

    def matchFlowTable(self, pkt, inport):
        pkt_attrs = of_util.extract_flow(pkt)
        pkt_attrs[core.IN_PORT] = inport
        self.communicationObjectUsed(self, "flowTable_read", pkt_attrs)
        matching_entries = []
        for entry in self.flow_table:
            if self.packetIsMatching(pkt, inport, entry.attrs):
                self.log.debug("*FTE: " + str(entry))
                matching_entries.append(entry)
            else:
                self.log.debug("FTE: " + str(entry))

        if len(matching_entries) == 0: # no match
            return False
        elif len(matching_entries) > 1: # multiple matches, select on priority
            matching_entries.sort(key=lambda x: x.priority, reverse=True)
        entry = matching_entries[0]
        self.processActions(pkt, entry.actions, inport)
        return True

    def processPacketOutMessage(self, command):
        self.log.debug("Processing a PacketOut: %s" % repr(command))
        if command.buffer_id != None:
            (packet, inport) = self.packet_store[command.buffer_id]
        else:
            packet = command.packet
            inport = command.inport

        if len(command.actions) > 0:
            self.processActions(packet, command.actions, inport)
        else:
            self.log.debug("Dropping packet with empty action list")
        if command.buffer_id != None:
            self.releaseBuffer(command.buffer_id)
        return

    def processFlowTableModification(self, command):
        self.communicationObjectUsed(self, "flowTable_write", command.arguments["attrs"])
        self.log.debug("Processing a FlowTableModification command: %s" % repr(command))
        if command.command == openflow.OFPFC_ADD:
            # TODO: idle_timeout, hard_timeout
            e = FlowTableEntry(command.arguments["attrs"], command.arguments["actions"], command.arguments["priority"])
            self.flow_table.append(e)
            self.flow_table.sort()
            if self.expire_entries:
                self.enableAction("expire_entry", e)
            # Process the packet specified in buffer_id
            buf_id = command.arguments["buffer_id"]
            if buf_id != None:
                if buf_id not in self.packet_store:
                    v = Violation(None, "Trying to access buffer %d %s" % (buf_id, self.packet_store))
                    self.state.reportViolation(v)
                (packet, inport) = self.packet_store[buf_id]
                self.matchFlowTable(packet, inport)
                self.releaseBuffer(buf_id)
        elif command.command == openflow.OFPFC_DELETE:
            attrs = command.arguments["attrs"]
            for e in self.flow_table:
                if e.attrs == attrs:
                    self.log.debug("Deleting flow entry %s" % e)
                    del self.flow_table[self.flow_table.index(e)]
                    if command.arguments.has_key("flags") and openflow.OFPFF_SEND_FLOW_REM in command.arguments["flags"]:
                        msg = openflow.OfpFlowRemoved()
                        msg.priority = e.priority
                        msg.reason = openflow.OFPRR_DELETE
                        msg.table_id = 0
                        msg.duration_sec = 0
                        msg.duration_nsec = 0
                        msg.idle_timeout = 0
                        msg.packet_count = 0
                        msg.byte_count = 0
                        msg.match = e.attrs # match attributes
                        self.state.model.controller.flowRemoved(msg)
        elif command.command == openflow.OFPFC_DELETE_STRICT:
            attrs = command.arguments["attrs"]
            priority = command.arguments["priority"]
            for e in self.flow_table:
                if e.attrs == attrs and e.priority == priority:
                    self.log.debug("Deleting flow entry %s" % e)
                    del self.flow_table[self.flow_table.index(e)]
                    if command.arguments.has_key("flags") and openflow.OFPFF_SEND_FLOW_REM in command.arguments["flags"]:
                        msg = openflow.OfpFlowRemoved()
                        msg.priority = e.priority
                        msg.reason = openflow.OFPRR_DELETE
                        msg.table_id = 0
                        msg.duration_sec = 0
                        msg.duration_nsec = 0
                        msg.idle_timeout = 0
                        msg.packet_count = 0
                        msg.byte_count = 0
                        msg.match = e.attrs # match attributes
                        self.state.model.controller.flowRemoved(msg)
                    break

    def acquireBuffer(self):
        if len(self.buffers) == 0:
            self.buffers.append(self.next_buffer_id)
            self.next_buffer_id = self.next_buffer_id + 1
        return self.buffers.pop()
    
    def releaseBuffer(self, buffer_id):
        del self.packet_store[buffer_id]
        self.buffers.append(buffer_id)

    def enqueueCommand(self, command):
        self.create_new_state()
        if self.this_switch_is_offline:
            self.state.model.controller.delSwitch(self)
            return # Drop and signal controller to fake drop of tcp connection
        self.command_queue.append(command)
        self.enableAction("process_command", skip_dup=True)
        self.state.testPoint("switch_enqueue_command", switch=self, command=command)
        self.log.debug("Queued command: %s" % repr(command))

    def expire_entry(self, entry):
        self.create_new_state()
        self.communicationObjectUsed(self, "flowTable_write", entry.attrs)
        del self.flow_table[self.flow_table.index(entry)]
        if entry.send_flow_rem:
            msg = openflow.OfpFlowRemoved()
            msg.priority = entry.priority
            msg.reason = openflow.OFPRR_HARD_TIMEOUT # could be also IDLE_TIMEOUT
            msg.table_id = 0
            msg.duration_sec = 0
            msg.duration_nsec = 0
            msg.idle_timeout = 0
            msg.packet_count = 0
            msg.byte_count = 0
            msg.match = entry.attrs # match attributes
            self.state.model.controller.flowRemoved(msg)
        return True

    def getWaitingPacket(self, port_name):
        port = self.ports[port_name]
        if len(port.in_buffer) > 0:
            pkt = port.in_buffer.pop(0)
            return pkt
        else:
            return None

    def sendQueryToController(self, pkt, port, reason, max_length = 1500):
        buffer_id = self.acquireBuffer()
        self.enqueueQueryToController(self.openflow_id, buffer_id, pkt, port, reason, max_length)
        self.packet_store[buffer_id] = (pkt, port)
        self.log.debug("Queued query to controller")

    def process_packet(self):
        """ Dequeues the first packet from all ports and processes it """
#       import pdb; pdb.set_trace()
        self.create_new_state()
        more_packets = False
        for p in self.ports:
            pkt = self.getWaitingPacket(p)
            if pkt == None:
                continue
            elif self.checkWaitingPacket(p):
                more_packets = True

            self.log.debug("Processing packet %s" % pkt)
            self.state.testPoint("switch_process_packet", switch=self, packet=pkt, port=p)

            if not self.matchFlowTable(pkt, p):
                self.sendQueryToController(pkt, p, openflow.OFPR_NO_MATCH)
        return not more_packets

    def process_command(self):
        """ Process a command from the controller """
        self.create_new_state()
        command = self.command_queue.pop(0)
        if isinstance(command, PacketOutMessage):
            self.processPacketOutMessage(command)
        elif isinstance(command, FlowTableModificationMessage):
            self.processFlowTableModification(command)
        else:
            utils.crash("Switch received an unknown command: %s" % command)
        return len(self.command_queue) == 0

    def create_new_state(self):
        if self.ALWAYS_NEW_STATE:
            self.state_cnt += 1

    def dump_equivalent_state(self):
        filtered_dict = Node.dump_equivalent_state(self)
        filtered_dict["command_queue"] = []
        for c in self.command_queue:
            utils.copy_state(c)
        filtered_dict["flow_table"] = utils.copy_state(self.flow_table)
        filtered_dict["packet_store"] = utils.copy_state(self.packet_store)

        if self.ALWAYS_NEW_STATE:
            filtered_dict["state_cnt"] = utils.copy_state(self.state_cnt)

        return filtered_dict

    def enqueueQueryToController(self, dp_id, buffer_id, packet, inport, reason, max_length):
        if max_length == 0:
            packet = ethernet()
        self.state.model.controller.enqueueQuery(dp_id, buffer_id, packet, inport, reason)

    def enqueuePacketToNode(self, node, packet, inport):
        node.enqueuePacket(packet, inport)


