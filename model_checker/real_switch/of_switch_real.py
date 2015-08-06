#
# Copyright (c) 2011, EPFL (Ecole Politechnique Federale de Lausanne)
# All rights reserved.
#
# Created by Marco Canini, Daniele Venzano, Dejan Kostic, Jennifer Rexford
# Contributed to this file: Maciej Kuzniar
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

from of_switch.of_switch import OpenflowSwitch
import comparator as Comparator

class OpenflowSwitchReal(OpenflowSwitch):
    def __init__(self, name, port_count, of_id, expire_entries=False, stop_when_no_match = False):
        OpenflowSwitch.__init__(self, name, port_count, of_id, expire_entries)
        self.bufferMap = {}
        self.newBuffers = []
        self.packetTranslator = None
        self.packetsSent = []
        self.queriesSent = []
        self.portMap = {}
        self.controllers = {}
        self.realIfaces = {}
        self.realOfIds = {}
        self.stop_when_no_match = stop_when_no_match
        
    def setRealSwitch(self, swType, controllerIp, controllerIface, portMap, real_of_id = -1, realIfaces = []):
        self.controllers[swType] = (controllerIp, controllerIface)
        self.portMap[swType] = portMap
        self.realIfaces[swType] = realIfaces[:]
        self.realOfIds[swType] = self.openflow_id + swType.value  if real_of_id == -1 else real_of_id + swType.value
        for i in range(0xfff8, 0xffff + 1):
            self.portMap[swType][i] = i

    def acquireBuffer(self):
        ret = OpenflowSwitch.acquireBuffer(self)
        self.newBuffers.append(ret)
        return ret

    def process_packet(self):
        del self.newBuffers[:]
        packetsToProcess = []
        for p in self.ports_object:             # if ports were used, DPOR would not work
            port = self.ports_object[p]
            pkt = None
            if len(port.in_buffer) > 0:
                pkt = port.in_buffer[0]
            if pkt is None:
                continue
            packetsToProcess.append((p, pkt))

        self.packetsSent = []
        self.queriesSent = []
        ret = OpenflowSwitch.process_packet(self)

        resultingPackets, resultingQueries = self.packetTranslator.processPacket(self, packetsToProcess, len(self.packetsSent) + len(self.queriesSent))

        for swtype in self.portMap:
            if swtype.type not in self.bufferMap:
                self.bufferMap[swtype.type] = {}
            for packet in resultingQueries[swtype.type]:
                for key in self.newBuffers:
                    (pkt, p) = self.packet_store[key]
                    if packet.in_port == self.portMap[swtype][p]:
                        self.bufferMap[swtype.type][key] = packet.buffer_id
                        break

        result, errors = Comparator.compareResults(self, resultingPackets, resultingQueries, self.packetsSent, self.queriesSent)
    
        if not result:
            self.state.testPoint("no_matching_packets")
            print errors
            print self.queriesSent
            print self.packetsSent
            print resultingPackets
            print resultingQueries
            assert not self.stop_when_no_match

        stats = self.packetTranslator.checkFlowStats(self)
        result, errors = Comparator.compareFlowStats(self, stats)
        if not result:
            self.state.testPoint("no_matching_packets")
            print errors
            print stats
            assert not self.stop_when_no_match

        stats = self.packetTranslator.checkPortStats(self)
        result, errors = Comparator.comparePortStats(self, stats)
        if not result:
            self.state.testPoint("no_matching_packets")
            print errors
            print stats
            assert not self.stop_when_no_match

        return ret
            
    def process_command(self):
        pp = self.command_queue[0];
        self.packetsSent = []
        self.queriesSent = []
        ret = OpenflowSwitch.process_command(self)

        resultingPackets, resultingQueries = self.packetTranslator.processCommand(self, pp, len(self.packetsSent) + len(self.queriesSent))
        
        result, errors = Comparator.compareResults(self, resultingPackets, resultingQueries, self.packetsSent, self.queriesSent)

        if not result:
            self.state.testPoint("no_matching_packets")
            print errors
            print self.queriesSent
            print self.packetsSent
            print resultingPackets
            print resultingQueries
            assert not self.stop_when_no_match

        return ret
            
    def start(self, model_checker):
        OpenflowSwitch.start(self, model_checker)
        self.packetTranslator = model_checker.packetTranslator

    def enqueueQueryToController(self, dp_id, buffer_id, packet, inport, reason, max_length):
        self.queriesSent.append((buffer_id, packet, inport, reason, max_length))
        OpenflowSwitch.enqueueQueryToController(self, dp_id, buffer_id, packet, inport, reason, max_length)

    def enqueuePacketToNode(self, node, packet, inport):
        self.packetsSent.append((node, inport, packet))
        OpenflowSwitch.enqueuePacketToNode(self, node, packet, inport)



