from threading import Thread, Event
import time

import nox.lib.openflow as openflow

from translator_utils import createTestPacket, createTestPacketIn, createScapyPacket

from scapy_mod import *

from virtual_switch import OpenFlowUserSwitch, OpenFlowKernelSwitch, OVSSwitch
from fake_controller import FakeController

from oftest.cstruct import *
from oftest.message import *
from oftest.action import * 
from oftest.action_list import *

class Stopper:
    def __init__(self):
        self.s = {}
        self.s[0] = False

    def stop(self):
        self.s[0] = True

    def start(self):
        self.s[0] = False

stopper = Stopper()

def shouldStopSniffing():
    return stopper.s[0]

global barrier_wait
global flow_stats_wait
global packet_wait
global lo_listening
global packet_wait_count

class PacketTranslator:
    def __init__(self, model, useBarrier = False, usePacket = True):
        self.model = model
        global barrier_wait , packet_wait, lo_listening, packet_wait_count, flow_stats_wait
        barrier_wait = {}
        packet_wait = {} 
        flow_stats_wait = {}
        packet_wait_count = {}
        lo_listening = Event()

        self.fakeController = None
        self.realSwitches = []
        self.realSwitchTypes = {}
        self.useBarrier = useBarrier
        self.usePacket = usePacket

        self.ctrlIfaces = [] #["eth0"]
        self.ctrlIps = [] #["128.178.149.155"]  # "127.0.0.1"
        self.usedSwitchTypes = []
        self.ifacesTypes = {}
        self.ifacesPorts = {}
        self.installedPacketRules = set([])

        for switch in self.model.switches:
            for key in switch.controllers.keys():
                if switch.controllers[key][1] not in self.ctrlIfaces:
                    self.ctrlIfaces.append(switch.controllers[key][1])
                if switch.controllers[key][0] not in self.ctrlIps:
                    self.ctrlIps.append(switch.controllers[key][0])
                if key not in self.usedSwitchTypes:
                    self.usedSwitchTypes.append(key)
                    barrier_wait[key.type] = Event()
                    flow_stats_wait[key.type] = Event()
                    packet_wait[key.type] = Event()
                    packet_wait_count[key.type] = 0
                p = 0
                for iface in switch.realIfaces[key]:
                    self.ifacesTypes[iface] = key.type
                    self.ifacesPorts[iface] = p
                    p += 1

        self.setEmptyValues()

    def setEmptyValues(self):
        self.interfacesMapping = {}
        self.interfacesListening = {}
        self.threads = []
        self.outgoingPackets = {}
        self.outgoingCommands = {}
        for sw in self.usedSwitchTypes:
            self.outgoingPackets[sw.type] = []
            self.outgoingCommands[sw.type] = []

        self.tcpPortsMap = {}
        self.installedPacketRules = set([])
        global barrier_wait , packet_wait, lo_listening, flow_stats_wait
        lo_listening.clear()
        for sw in self.usedSwitchTypes:
            barrier_wait[sw.type].clear()
            flow_stats_wait[sw.type].clear()
            packet_wait[sw.type].clear()
            packet_wait_count[sw.type] = 0


    def getNodeInterfaces(self, realSwitch, switch):
        interfaces = []
        for port in switch.ports_object.keys():
            interfaces.append(switch.name + "-" + realSwitch.type + "-eth" + str(switch.ports_object[port].name) + "-f")
        return interfaces

    def getFakeInterfaces(self, switch, type):
        if len(switch.realIfaces[type]) > 0:    #HP
            return switch.realIfaces[type]

        ifaces = []
        for port in switch.ports_object.keys():
            if switch.ports_object[port].peer is not None:
                ifaces.append(switch.name + "-" + type.type + "-eth"+str(switch.ports_object[port].name) + "-f")
        return ifaces

    def initTopo(self):
        ifaces = []

        for ctrl in self.ctrlIfaces:
            ifaces.append( (ctrl, "tcp dst port %d" % 6633) )

        self.interfacesListening["ctrl"] = False
        for switch in self.model.switches:
            for real_switch in switch.portMap.keys():
                for iface in self.getFakeInterfaces(switch, real_switch):
                    if iface == "":
                        continue
                    self.interfacesListening[iface] = False
                    ifaces.append( (iface, None) )

        stopper.start()

        if self.fakeController is None:
            self.fakeController = FakeController(shouldStopSniffing, self.ctrlIps, self.useBarrier, self.usePacket)

        if len(self.realSwitches) == 0:
            for sw in self.model.switches:
                for real_sw in sw.portMap.keys():
                    rs = real_sw(sw, sw.controllers[real_sw][0], 6633)
                    self.realSwitches.append(rs)
                    self.realSwitchTypes[sw.realOfIds[real_sw]] = real_sw.type

            for sw in self.realSwitches:
                sw.createVirtualInterfaces()

        global lo_listening
        lo_listening.clear()

        t = Thread(target = mysniff, kwargs = {"ifaces" : ifaces, "prn" : lambda x, y: self.processSnifedPacket(x, y), "shouldStop" : shouldStopSniffing, "timeout" : 0.1, "lo_listening" : lo_listening})
        self.threads.append(t)
        t.start()
        lo_listening.wait()
        lo_listening.clear()

        self.fakeController.restart()
        t = self.fakeController.startSniffing()
        self.threads.append(t)
        
        for sw in self.realSwitches:
            sw.init()

        self.startSniffing()


    def destroyTopo(self, finalize=True):
        self.stopSniffing()
        for thread in self.threads:
            thread.join()
        if self.fakeController is not None:
            self.fakeController.stop()
        for sw in self.realSwitches:
            sw.clean()
            if finalize:
                sw.removeVirtualInterfaces()

    def restartTopo(self):
        self.destroyTopo(False)
        self.setEmptyValues()
        self.initTopo()

    def stopSniffing(self):
        stopper.stop()

    def startSniffing(self):
        stopper.start()

    def getSwitchType(self, iface):
        if iface in self.ifacesTypes:
            return self.ifacesTypes[iface]
        else:
            names =  iface.split("-")       #HP
            return names[1]

    def getPortNumber(self, iface):
        if iface in self.ifacesPorts:
            return self.ifacesPorts[iface]
        else:
            names =  iface.split("-")       #HP
            return int(names[2][3:])

    def processSnifedPacket(self, packet, iface):
        if iface[0] in self.ctrlIfaces:
            self.processSniffedPacketToController(packet, iface)
            return

        if not self.interfacesListening[iface[0]] or Ether not in packet:
            return

        if self.usePacket and packet[Ether].src == "55:55:55:55:55:55":
            global packet_wait, packet_wait_count
            packet_wait_count[self.getSwitchType(iface[0])] -= 1
            if packet_wait_count[self.getSwitchType(iface[0])] == 0:
                packet_wait[self.getSwitchType(iface[0])].set()
            return

        if not self.useBarrier and packet[Ether].src == "66:66:66:66:66:66":
            global barrier_wait
            barrier_wait[self.getSwitchType(iface[0])].set()
            return

        self.outgoingPackets[self.getSwitchType(iface[0])].append((self.getPortNumber(iface[0]), packet))
    

    def processSniffedPacketToController(self, packet, iface):
        if Raw in packet:                       #there is openflow data
            of_version, of_type, of_len = struct.unpack('!BBH',packet[Raw].load[:4])
            if of_type == 1:                    #error
                print "ERROR", packet[IP].src
            elif of_type == 6:                  # features replay contains datapath id
                if len(filter(lambda x : self.tcpPortsMap[x][0] == packet[IP].src and self.tcpPortsMap[x][1] == packet[TCP].sport, self.tcpPortsMap.keys())) == 0:  
                    of_datapath_id = struct.unpack('!Q',packet[Raw].load[8:16])[0]
                    self.tcpPortsMap[of_datapath_id] = (packet[IP].src, packet[TCP].sport)
            elif of_len > 8 and of_type == 10:  # packet_in
                if not self.interfacesListening["ctrl"]:
                    return
                p = packet_in()
                p.unpack(packet[Raw].load)                  
                type = self.realSwitchTypes[filter(lambda x : self.tcpPortsMap[x][0] == packet[IP].src and self.tcpPortsMap[x][1] == packet[TCP].sport, self.tcpPortsMap.keys())[0]]
                if self.usePacket and len(p.data) > 12 and struct.unpack('6B', p.data[6:12]) == (136, 136, 136, 136, 136, 136):
                    global packet_wait, packet_wait_count
                    packet_wait_count[type] -= 1
                    if packet_wait_count[type] == 0:
                        packet_wait[type].set()
                    return
#               if not self.useBarrier and p.reason == openflow.OFPR_ACTION and p.in_port == 0 and len(str(p.data)) > 11 and str(p.data)[6:11] == "ffffff":
#                   global barrier_wait
#                   self.installedPacketRules.add(filter(lambda x : self.tcpPortsMap[x][0] == packet[IP].src and self.tcpPortsMap[x][1] == packet[TCP].sport, self.tcpPortsMap.keys())[0])
#                   barrier_wait[type].set()
#               else:
                self.outgoingCommands[type].append(p)
            elif self.useBarrier and of_type == 19:                 # barrier_response
                global barrier_wait
                type = self.realSwitchTypes[filter(lambda x : self.tcpPortsMap[x][0] == packet[IP].src and self.tcpPortsMap[x][1] == packet[TCP].sport, self.tcpPortsMap.keys())[0]]
#               self.installedPacketRules.add(filter(lambda x : self.tcpPortsMap[x][0] == packet[IP].src and self.tcpPortsMap[x][1] == packet[TCP].sport, self.tcpPortsMap.keys())[0])
                barrier_wait[type].set()
            elif of_type == 11:                                     #flow removed
                p = flow_removed()
                p.unpack(packet[Raw].load)
                if p.match.dl_src == [119, 119, 119, 119, 119, 119]:
                    self.installedPacketRules.add(filter(lambda x : self.tcpPortsMap[x][0] == packet[IP].src and self.tcpPortsMap[x][1] == packet[TCP].sport, self.tcpPortsMap.keys())[0])
            elif of_type == 17:                                     # OFPT_STATS_REPLY
                type = self.realSwitchTypes[filter(lambda x : self.tcpPortsMap[x][0] == packet[IP].src and self.tcpPortsMap[x][1] == packet[TCP].sport, self.tcpPortsMap.keys())[0]]
                stat_type = struct.unpack('H',packet[Raw].load[9:9+2])
                if stat_type[0] == OFPST_PORT:
                    p = port_stats_reply()
                    p.unpack(packet[Raw].load)
                    self.outgoingCommands[type].append(p)
                elif stat_type[0] == OFPST_FLOW:
                    p = flow_stats_reply()
                    p.unpack(packet[Raw].load)
                    self.outgoingCommands[type].append(p)
                global flow_stats_wait
                flow_stats_wait[type].set()

        elif packet[TCP].flags & 4 != 0:        #TCP RST - don't send anything until new connection is established
            q = filter(lambda x : self.tcpPortsMap[x][0] == packet[IP].src and self.tcpPortsMap[x][1] == packet[TCP].sport, self.tcpPortsMap.keys())
            if len(q) > 0:
                del self.tcpPortsMap[q[0]]
                self.installedPacketRules.remove(q[0])

            
    def enqueuePacket(self, switch, port, packet, fake = False):
        for sw in switch.portMap.keys():
            while int(switch.realOfIds[sw]) not in self.tcpPortsMap.keys() or int(switch.realOfIds[sw]) not in self.installedPacketRules:
                time.sleep(0.02)

            interface = ""
            if len(switch.realIfaces[sw]) == 0:
                interface = switch.name + "-" + sw.type + "-eth" + str(port) + "-f"
            else:                   #HP
                interface = switch.realIfaces[sw][port]

            sendp(createScapyPacket(packet), iface=interface)
        
            if self.usePacket and not fake:
                global packet_wait_count
                packet_wait_count[sw.type] += 2

    
    def setListening(self, val, switch):
        for sw in switch.portMap.keys():
            for interface in self.getFakeInterfaces(switch, sw):
                self.interfacesListening[interface] = val
            self.outgoingPackets[sw.type] = []
            self.outgoingCommands[sw.type] = []
        self.interfacesListening["ctrl"] = val  


    def processPacket(self, switch, packets, expectedCount):
        self.setListening(True, switch)

        for (port, packet) in packets:
            self.enqueuePacket(switch, port, packet)
            
        if self.usePacket:
            for (port, packet) in packets:
                self.enqueuePacket(switch, port, createTestPacket(), True)
                self.enqueuePacket(switch, port, createTestPacketIn(), True)

        if not self.usePacket:
            time.sleep(0.2)
            for sw in switch.portMap.keys():
                while len(self.outgoingPackets[sw.type]) + len(self.outgoingCommands[sw.type]) < expectedCount:
                    time.sleep(0.02)            #TODO: change to notify
        else:
            global packet_wait
            for sw in switch.portMap.keys():
                packet_wait[sw.type].wait(5)
                packet_wait[sw.type].clear()

        outgoingPackets = {}
        outgoingCommands = {}

        for sw in switch.portMap.keys():
            outgoingPackets[sw.type] = self.outgoingPackets[sw.type][:]
            outgoingCommands[sw.type] = self.outgoingCommands[sw.type][:]

        self.setListening(False, switch)

        return outgoingPackets, outgoingCommands


    def processCommand(self, switch, command, expectedCount):
        self.setListening(True, switch)
    
        global barrier_wait
        for sw in switch.portMap.keys():
            while int(switch.realOfIds[sw]) not in self.tcpPortsMap.keys() or int(switch.realOfIds[sw]) not in self.installedPacketRules:
                time.sleep(0.02)                                #TODO: notify?
            
            barrier_wait[sw.type].clear()
            self.fakeController.enqueuePacketsToSend(sw, switch, command, self.tcpPortsMap[switch.realOfIds[sw]])

        for sw in switch.portMap.keys():
            barrier_wait[sw.type].wait(5)
            barrier_wait[sw.type].clear()

        outgoingPackets = {}
        outgoingCommands = {}

        for sw in switch.portMap.keys():
            outgoingPackets[sw.type] = self.outgoingPackets[sw.type][:]
            outgoingCommands[sw.type] = self.outgoingCommands[sw.type][:]

        self.setListening(False, switch)

        return outgoingPackets, outgoingCommands


    def checkFlowStats(self, switch):
        return self.checkStats(switch, "flow_stats")

    def checkPortStats(self, switch):
        return self.checkStats(switch, "port_stats")    

    def checkStats(self, switch, command):
        self.setListening(False, switch)
        global flow_stats_wait
        for sw in switch.portMap.keys():
            while int(switch.realOfIds[sw]) not in self.tcpPortsMap.keys() or int(switch.realOfIds[sw]) not in self.installedPacketRules:
                time.sleep(0.02)                                #TODO: notify?
            
            flow_stats_wait[sw.type].clear()
            self.fakeController.enqueuePacketsToSend(sw, switch, command, self.tcpPortsMap[switch.realOfIds[sw]])

        for sw in switch.portMap.keys():
            flow_stats_wait[sw.type].wait(5)
            flow_stats_wait[sw.type].clear()

        stats = {}

        for sw in switch.portMap.keys():
            stats[sw.type] = self.outgoingCommands[sw.type][0]

        self.setListening(False, switch)
        
        return stats


