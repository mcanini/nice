import socket
from select import select
from threading import Thread

from translator_utils import createMatch, createBarrierPacket

from lib.of_packet_out_message import PacketOutMessage
from lib.of_flow_table_modification_message import FlowTableModificationMessage

import nox.lib.core as core
import nox.lib.openflow as openflow

from oftest.cstruct import *
from oftest.message import *
from oftest.action import * 
from oftest.action_list import *


class FakeController:
    def __init__(self, shouldStopSniffing, ips, useBarrier, useNewPacket):
        self.ctrlSockets = []
        self.waitingPackets = []
        self.portMap = {}

        for ip in ips:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setblocking(0)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            s.bind((ip, 6633))
            s.listen(20)
            self.ctrlSockets.append(s)

        self.sockets = self.ctrlSockets[:]
        self.shouldStopSniffing = shouldStopSniffing
        self.useBarrier = useBarrier
        self.useNewPacket = useNewPacket


    def restart(self):
        del self.waitingPackets[:]
        self.portMap.clear()
        del self.sockets[:]
        self.sockets = self.ctrlSockets[:]

    def startSniffing(self):
        t1 = Thread(target=self.processPackets)
        t1.start()
        return t1

    def prepareBarrierPacket(self, switch, switch_type):
        if self.useBarrier:
            barrier = barrier_request()
            return barrier.pack()
        else:
#           out = PacketOutMessage(None, createBarrierPacket(), [[openflow.OFPAT_OUTPUT, [27, openflow.OFPP_CONTROLLER]]], openflow.OFPP_CONTROLLER)
            port1 = 0
            for p in switch.ports_object.keys():
                if switch.ports_object[p].peer is not None:
                    port1 = p
            out = PacketOutMessage(None, createBarrierPacket(), [[openflow.OFPAT_OUTPUT, [27, port1]]], openflow.OFPP_CONTROLLER)
            return self.translatePacketOut(switch_type, switch, out)        

    def enqueuePacketsToSend(self, switch_type, switch, command, port):
        packet = ""
        if isinstance(command, PacketOutMessage):
            packet = self.translatePacketOut(switch_type, switch, command)
        elif isinstance(command, FlowTableModificationMessage):
            packet = self.translateFlowMod(switch_type, switch, command)
        elif type(command) == type("") and command == "flow_stats":
            packet = self.translateFlowStatsRequest(switch_type, switch, command)
            self.waitingPackets.append((port, packet))
            return
        elif type(command) == type("") and command == "port_stats":
            packet = self.translatePortStatsRequest(switch_type, switch, command)
            self.waitingPackets.append((port, packet))
            return

        self.waitingPackets.append((port, packet))
        self.waitingPackets.append( (port, self.prepareBarrierPacket(switch, switch_type) ) )

    def translatePacketOut(self, switch_type, switch, pkt):
        out = packet_out()
        if pkt.buffer_id is not None:
            out.buffer_id = switch.bufferMap[switch_type.type][pkt.buffer_id]
            out.in_port = switch.portMap[switch_type][pkt.inport]
        else:
            out.buffer_id = -1
            p, data = pkt.packet.toScapy()
            p = p/data if data is not None else p
            out.data = str(p)
            out.in_port = switch.portMap[switch_type][pkt.inport]   
        for action in pkt.actions:
            if action[0] == openflow.OFPAT_OUTPUT:
                a = action_output()
                a.port = switch.portMap[switch_type][action[1][1]]
                a.max_len = action[1][0]
                out.actions.add(a)

        translated = out.pack()
        return translated

    def translateFlowMod(self, switch_type, switch, pkt):
        out = flow_mod()
        out.hard_timeout = openflow.OFP_FLOW_PERMANENT
        out.idle_timeout = openflow.OFP_FLOW_PERMANENT
        out.command = pkt.command
        out.out_port = 0xffff
        if "buffer_id" in pkt.arguments and pkt.arguments["buffer_id"] is not None:
            out.buffer_id = switch.bufferMap[switch_type.type][pkt.arguments["buffer_id"]]
        else:
            out.buffer_id = 0xffffffff
        if "attrs" in pkt.arguments:
            out.match = createMatch(pkt.arguments["attrs"])
            if out.match.in_port in switch.portMap[switch_type]:
                out.match.in_port = switch.portMap[switch_type][out.match.in_port]
        if "priority" in pkt.arguments:
            out.priority = pkt.arguments["priority"]
        if "actions" in pkt.arguments:
            for action in pkt.arguments["actions"]:
                if action[0] == openflow.OFPAT_OUTPUT:
                    a = action_output()
                    a.port = switch.portMap[switch_type][action[1][1]]
                    a.max_len = action[1][0]
                    out.actions.add(a)

        return out.pack()

    def translateFlowStatsRequest(self, switch_type, switch, pkt):
        out = flow_stats_request()
        out.out_port = openflow.OFPP_NONE
        out.table_id = 0xff
        out.match = createMatch({})
        translated = out.pack()
        return translated

    def translatePortStatsRequest(self, switch_type, switch, pkt):
        out = port_stats_request()
        out.port_no = openflow.OFPP_NONE
        translated = out.pack()
        return translated

    def sendWaitingPackets(self):
        while len(self.waitingPackets) > 0:
            (port, packet) = self.waitingPackets.pop(0)
            self.portMap[port].sendall(packet)

    def processPackets(self):
        while not self.shouldStopSniffing():
            self.sendWaitingPackets()
            a,b,c = select(self.sockets,[],[], 0.1)
            for socket in a:
                try:
                    if socket in self.ctrlSockets:
                        switchSocket, addr = socket.accept()
                        switchSocket.setblocking(0)
                        self.sockets.append(switchSocket)
                        self.portMap[(addr[0], addr[1])] = switchSocket
                    else:
                        pkt = socket.recv(1500)
                        self.interpretPacket(socket, pkt)
                except IOError, e:
                    pass
                    

    def interpretPacket(self, socket, pkt):
        if pkt is None or len(pkt) == 0:
            return

        _, t, l, xid = struct.unpack('!BBHI', pkt[:8])
            
        if t == 0:          #hello
            try:
                socket.sendall(struct.pack('!BBHI', 1,0,8,xid)) # hello
                socket.sendall(struct.pack('!BBHI', 1,5,8,0))   # features request
            except IOError, e:
                pass
        if t == 2:          #echo request
            socket.sendall(struct.pack('!BBHI', 1,3,8,xid))     # echo response
        if t == 6:          #features response  
            out = flow_mod()
            out.buffer_id = 0xffffffff
            out.priority = 0xffff
            attrs = {}
            out.match = createMatch(attrs)
            out.command = 3                             #del all
            out.out_port = 0xffff
            socket.sendall(out.pack())  
            if self.useNewPacket:
                out = flow_mod()
                out.hard_timeout = openflow.OFP_FLOW_PERMANENT
                out.idle_timeout = openflow.OFP_FLOW_PERMANENT
                out.buffer_id = 0xffffffff
                out.priority = 0xffff
                attrs = {}
                attrs[core.DL_SRC] = "55:55:55:55:55:55"
                out.match = createMatch(attrs)
                a = action_output()
                a.port = openflow.OFPP_IN_PORT
                out.actions.add(a)
                socket.sendall(out.pack())                      # packet testing flow

                out4 = flow_mod()
                out4.hard_timeout = openflow.OFP_FLOW_PERMANENT
                out4.idle_timeout = openflow.OFP_FLOW_PERMANENT
                out4.buffer_id = 0xffffffff
                out4.priority = 0xffff
                attrs = {}
                attrs[core.DL_SRC] = "88:88:88:88:88:88"
                out4.match = createMatch(attrs)
                a = action_output()
                a.port = openflow.OFPP_CONTROLLER
                a.max_len = 10000
                out4.actions.add(a)
                socket.sendall(out4.pack())                         # packet testing flow 2

                out2 = flow_mod()
                out2.hard_timeout = openflow.OFP_FLOW_PERMANENT
                out2.idle_timeout = openflow.OFP_FLOW_PERMANENT
                out2.buffer_id = 0xffffffff
                out2.priority = 0xffff
                out2.flags = 1
                attrs = {}
                attrs[core.DL_SRC] = "77:77:77:77:77:77"
                out2.match = createMatch(attrs)
                socket.sendall(out2.pack())

                out3 = flow_mod()
                out3.hard_timeout = openflow.OFP_FLOW_PERMANENT
                out3.idle_timeout = openflow.OFP_FLOW_PERMANENT
                out3.buffer_id = 0xffffffff
                out3.priority = 0xffff
                out3.flags = 1
                attrs = {}
                attrs[core.DL_SRC] = "77:77:77:77:77:77"
                out3.match = createMatch(attrs)
                out3.command = 3                                #del
                out3.out_port = 0xffff
                socket.sendall(out3.pack())


    def stop(self):
        for socket in self.sockets:
            if socket not in self.ctrlSockets:
                socket.close()
#       self.socket.close()

