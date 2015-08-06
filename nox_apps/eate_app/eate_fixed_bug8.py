#
# Copyright (c) 2011, EPFL (Ecole Politechnique Federale de Lausanne)
# All rights reserved.
#
# Created by Marco Canini, Daniele Venzano, Dejan Kostic
# To this file contributed: Peter Peresini
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

from nox.lib.core     import *
from nox.lib.util     import *
from nox.lib.packet.ethernet     import ethernet
from nox.lib.packet.packet_utils import mac_to_str, mac_to_int

from twisted.python import log

import logging
from time import time
from socket import htons
from struct import unpack

#  from switch statistics
from nox.lib.core import *

from collections import defaultdict

import nox.lib.openflow as openflow
from nox.lib.packet.packet_utils  import mac_to_str

#from nox.lib.netinet.netinet import datapathid,create_ipaddr,c_htonl
from twisted.python import log

#from nox.coreapps.pyrt.pycomponent import Table_stats_in_event, Aggregate_stats_in_event
#from nox.lib.openflow import OFPST_TABLE,  OFPST_PORT, ofp_match, OFPP_NONE
from nox.lib.openflow import OFPP_NONE
from nox.lib.packet.ethernet     import ethernet

logger = logging.getLogger('nox.coreapps.examples.eate')

# Global eate instance 
inst = None

# Timeout for cached MAC entries
CACHE_TIMEOUT = 5

#Various voodoo constants

#wait time in seconds after a stat query is sent to all the ports
WAIT_FOR_RESULTS = 10   
# wait time in seconds between 2 stats measurements
WAIT_BEFOR_NEXT_MEASURE = 2
BANDWIDTH = 1#Gbits/s
ETHERNET_MTU = 1500  # Bytes
MAX_PACKETS_PER_SECOND = (BANDWIDTH * 1000000)/(ETHERNET_MTU * 8)

# Number of packet between 2 stats measurements that will imply to change the route of new packet to avoid congestion
REAL_TRESHOLD = 0.8 * MAX_PACKETS_PER_SECOND * (WAIT_BEFOR_NEXT_MEASURE + WAIT_FOR_RESULTS)

# these values correspond to the  utilization of the link between switches
# five and six in mininet. 2 flows are needed to cross the high threshold
MEDIUM_THRESHOLD = 500000000 # bytes 
HIGH_THRESHOLD = 1000000000 # bytes 

#  from switch statistics
DEFAULT_POLL_TABLE_PERIOD     = 5
DEFAULT_POLL_PORT_PERIOD      = 5
DEFAULT_POLL_AGGREGATE_PERIOD = 5

def datapath_leave_callback(dpid):
    logger.info('Switch %x has left the network' % dpid)
#     if inst.st.has_key(dpid):
#         del inst.st[dpid]

def datapath_join_callback(dpid, stats):
    logger.info('Switch %x has joined the network' % dpid)

# --
# Packet entry method.
# Drop LLDP packets (or we get confused) and attempt learning and
# forwarding
# --
def packet_in_callback(dpid, inport, reason, len, bufid, packet):

    if not packet.parsed:
        logger.info('Ignoring incomplete packet')

#     if not inst.st.has_key(dpid):
#         logger.info('registering new switch %x' % dpid)
#         inst.st[dpid] = {}

    # don't forward lldp packets    
    if packet.type == ethernet.LLDP_TYPE:
        logger.info('Ignoring LLDP packet')
        return CONTINUE

    inst.forward_l2_packet(dpid, inport, packet, packet.arr, bufid)
    inst.install_path(dpid, inport, packet, packet.arr, bufid)

    return CONTINUE

class eate(Component):


    def deployRules(self):
        # All these rules are based on the always-on paths
        inst.switchPath['00:00:00:00:00:0B'] = {}
        inst.switchPath['00:00:00:00:00:0D'] = {}
        inst.switchPath['00:00:00:00:00:0E'] = {}

        inst.alwaysOnPath['00:00:00:00:00:0B'] = {}
        inst.alwaysOnPath['00:00:00:00:00:0D'] = {}
        inst.alwaysOnPath['00:00:00:00:00:0E'] = {}


        inst.alwaysOnPath['00:00:00:00:00:0B']['00:00:00:00:00:0D'] = [1, 2]
        inst.alwaysOnPath['00:00:00:00:00:0B']['00:00:00:00:00:0E'] = [1, 2]
        inst.alwaysOnPath['00:00:00:00:00:0D']['00:00:00:00:00:0B'] = [2, 1]
        inst.alwaysOnPath['00:00:00:00:00:0D']['00:00:00:00:00:0E'] = [2]
        inst.alwaysOnPath['00:00:00:00:00:0E']['00:00:00:00:00:0B'] = [2, 1]
        inst.alwaysOnPath['00:00:00:00:00:0E']['00:00:00:00:00:0D'] = [2, 1]

        inst.onDemandPath['00:00:00:00:00:0B'] = {}
        inst.onDemandPath['00:00:00:00:00:0D'] = {}
        inst.onDemandPath['00:00:00:00:00:0E'] = {}

        inst.onDemandPath['00:00:00:00:00:0B']['00:00:00:00:00:0D'] = [1, 3, 2]
        inst.onDemandPath['00:00:00:00:00:0B']['00:00:00:00:00:0E'] = [1, 3, 2]
        inst.onDemandPath['00:00:00:00:00:0D']['00:00:00:00:00:0B'] = [2, 3, 1]
        inst.onDemandPath['00:00:00:00:00:0D']['00:00:00:00:00:0E'] = [2]
        inst.onDemandPath['00:00:00:00:00:0E']['00:00:00:00:00:0B'] = [2, 3, 1]
        inst.onDemandPath['00:00:00:00:00:0E']['00:00:00:00:00:0D'] = [2]

        inst.switches = [1, 2, 3]

        inst.hosts = ['00:00:00:00:00:0B', '00:00:00:00:00:0D', '00:00:00:00:00:0E']

        #Rules for switch 1
        inst.onDemandMap[1] = {}
        inst.onDemandMap[1]['00:00:00:00:00:0B']=3
        inst.onDemandMap[1]['00:00:00:00:00:0D']=1
        inst.onDemandMap[1]['00:00:00:00:00:0E']=1

        #Rules for switch 2
        inst.onDemandMap[2] = {}
        inst.onDemandMap[2]['00:00:00:00:00:0B']=2
        inst.onDemandMap[2]['00:00:00:00:00:0D']=3
        inst.onDemandMap[2]['00:00:00:00:00:0E']=4

        #Rules for switch 3
        inst.onDemandMap[3] = {}
        inst.onDemandMap[3]['00:00:00:00:00:0B']=1
        inst.onDemandMap[3]['00:00:00:00:00:0D']=2
        inst.onDemandMap[3]['00:00:00:00:00:0E']=2

        #Rules for switch 1
        inst.alwaysOnMap[1] = {}
        inst.alwaysOnMap[1]['00:00:00:00:00:0B']=3
        inst.alwaysOnMap[1]['00:00:00:00:00:0D']=2
        inst.alwaysOnMap[1]['00:00:00:00:00:0E']=2

        #Rules for switch 2
        inst.alwaysOnMap[2] = {}
        inst.alwaysOnMap[2]['00:00:00:00:00:0B']=1
        inst.alwaysOnMap[2]['00:00:00:00:00:0D']=3
        inst.alwaysOnMap[2]['00:00:00:00:00:0E']=4

        #Rules for switch 3
        inst.alwaysOnMap[3] = {}
        inst.alwaysOnMap[3]['00:00:00:00:00:0B']=1
        inst.alwaysOnMap[3]['00:00:00:00:00:0D']=2
        inst.alwaysOnMap[3]['00:00:00:00:00:0E']=2

        #the default is always on. ARP packets always use it
        for s in inst.switches:
            inst.switchPortMap[s]={}
            for dst in inst.hosts:
#             print s, dst
                inst.switchPortMap[s][dst]=inst.alwaysOnMap[s][dst]

        for src in inst.hosts:
            for dst in inst.hosts:
                if src == dst:
                    continue
                inst.switchPath[src][dst] = inst.alwaysOnPath[src][dst]

        logger.info('Rules set' )

    def choose_path(self, srcip, dstip):    
        choice="alwaysOn"
        # it is silly if the path in the other direction is going through
        # a different route,  equipment may not be able to sleep.

        #  however, this code is not paying attention  to the direction of the flow
        #  source and destination might have different modulo values
        if inst.energyLtoR == "alwaysOn" and inst.energyRtoL == "alwaysOn":
            logger.info('alwaysOn only %s' % dstip)
        elif dstip % 2 == 0:
            logger.info('alwaysOn or onDemand -> alwaysOn, modulo 2 choice 1 %s' % dstip)
        elif dstip % 2 == 1:
            logger.info('alwaysOn or onDemand -> onDemand, modulo 2 choice 0 %s' % dstip)
            # we are here because either direction is on demand  and the
            # destination based  choice allows us to send over on demand
            # check if the load is high enough.  if not, send some on always on
#             if (inst.onDemandLevelLtoR != "high" and inst.onDemandLevelRtoL != "high") and srcip % 2 == 0:
#                 logger.info('alwaysOn or onDemand -> alwaysOn, medium modulo 2 choice 0 %s' % srcip)
#                 choice="alwaysOn"
#             else:
#                 logger.info('alwaysOn or onDemand -> onDemand, medium modulo 2 choice 1 %s' % srcip)
            choice="onDemand"
        return choice

    def forward_l2_packet(self, dpid, inport, packet, buf, bufid):
        logger.info('%d forward_l2_packet for type %s' % (dpid, str(packet.type)))
        if packet.type == ethernet.ARP_TYPE:
            dstip = packet.next.protodst
            choice = "alwaysOn"
        # commenting these two lines will cause  packets at intermediate switches to be dropped    
        #elif packet.type == ethernet.IP_TYPE:
        #    dstip = packet.next.dstip
        #    srcip = packet.next.srcip
        #    choice=inst.choose_path(srcip, dstip)
        else:
            logger.info('Ignoring non ARP packet %s' % str(packet.type))
            return

        dstaddr=self.getMac(dstip)
        logger.info('forward_l2_packet for dstip %s dstaddr %s' % (dstip,dstaddr))
        if not ord(dstaddr[0]) & 1 and inst.switchPortMap[dpid].has_key(dstaddr):
            if choice == "onDemand":
                prt = inst.onDemandMap[dpid][dstaddr]
            else:
                prt = inst.alwaysOnMap[dpid][dstaddr]
            # bug: not paying attention to the choice for individual packets
            #prt = inst.alwaysOnMap[dpid][dstaddr]
            
            logger.info('Forwarding Table changed')
            flow = extract_flow(packet)
            flow[core.IN_PORT] = inport
#         if packet.type == ethernet.IP_TYPE:
#             print flow
#         inst.send_openflow(dpid, bufid, buf, prt, inport)
            actions = [[openflow.OFPAT_OUTPUT, [0, prt]]]
            inst.install_datapath_flow(dpid, flow, CACHE_TIMEOUT, 
                                       openflow.OFP_FLOW_PERMANENT, actions,
                                       bufid, openflow.OFP_DEFAULT_PRIORITY,
                                       inport, buf)

    def install_path(self, dpid, incoming_port, packet, buf, bufid):    
        logger.info('%d install_path for type %s' % (dpid, str(packet.type)))
        if packet.type == ethernet.ARP_TYPE:
            logger.info('Ignoring ARP packet %s' % str(packet.type))
            inst.lastSwitchList=[]
            return
        elif packet.type == ethernet.IP_TYPE:
            dstip = packet.next.dstip
            srcip = packet.next.srcip
        else:
            logger.info('Ignoring non IP packet %s' % str(packet.type))
            inst.lastSwitchList=[]
            return

        dstaddr=self.getMac(dstip)
        srcaddr=self.getMac(srcip)
        logger.info('install_path for dstip %s dstaddr %s srcip %s srcaddr %s' % (dstip,dstaddr,srcip,srcaddr))

        if ((not ord(dstaddr[0]) & 1) and inst.switchPortMap[dpid].has_key(dstaddr) and
            inst.switchPortMap[dpid].has_key(dstaddr) and 
            inst.switchPath[srcaddr][dstaddr][0] == dpid):
            # if inst.switchPath[srcitaddr][dstaddr] == inst.alwaysOnPath[srcaddr][dstaddr]:
            # things do not work if flows hit the existing rules even though they
            # want to go over always on. switchPath  would point to the wrong value

            choice=self.choose_path (srcip, dstip)

            #  however, this code is not paying attention  to the direction of the flow
            #  source and destination might have different modulo values
            switchList=inst.alwaysOnPath[srcaddr][dstaddr]
            if choice == "onDemand":
                switchList=inst.onDemandPath[srcaddr][dstaddr]
            # # this is the equivalent of the nosplit bug    
            # switchList=inst.onDemandPath[srcaddr][dstaddr]
            logger.info('Preinstalling %s: %s' % (choice, switchList))       
            flow = extract_flow(packet)
#        print flow
            for s in switchList:
                if choice == "onDemand":
                    outport = inst.onDemandMap[s][dstaddr]
                    inport = inst.onDemandMap[s][srcaddr]
                    # this is the bug with the switchMap
                    # inport = inst.onDemandMap[s][dstaddr]
                    # outport = inst.onDemandMap[s][srcaddr]
                else:
                    outport = inst.alwaysOnMap[s][dstaddr]
                    inport = inst.alwaysOnMap[s][srcaddr]

#             logger.info('Preinstalling on %s (in %d), %d -> %d' % (s, incoming_port, inport, outport))
                actions = [[openflow.OFPAT_OUTPUT, [0, outport]]]
                if s != dpid:       # fix bug VIII
                    inst.install_datapath_flow(s, flow, CACHE_TIMEOUT, 
                                               openflow.OFP_FLOW_PERMANENT, actions,
                                               None, openflow.OFP_DEFAULT_PRIORITY,
                                               None, None)
                else:
                    inst.install_datapath_flow(s, flow, CACHE_TIMEOUT,
                                               openflow.OFP_FLOW_PERMANENT, actions,
                                               bufid, openflow.OFP_DEFAULT_PRIORITY,
                                               incoming_port, packet)
                inst.lastSwitchList=switchList

#             if s == dpid:
#                 logger.info('Forwarding packet on %s' % s)
#                 flow[core.IN_PORT] = incoming_port
#                 inst.send_openflow(dpid, bufid, buf, outport, incoming_port)


#This method return the mac address of the destination IP. This avoid broadcasting the packet to all ports
#since the source doesn't know the mac address of the destination for the first packet
#Hardcoded ARP information
    def getMac(self, networkDestination) :
        if networkDestination == 167772171:
            MAC="00:00:00:00:00:0B"
        elif networkDestination == 167772172:
            MAC="00:00:00:00:00:0C"
        elif networkDestination == 167772173:
            MAC="00:00:00:00:00:0D"
        elif networkDestination == 167772174:
            MAC="00:00:00:00:00:0E"
        else:
            MAC="00:00:00:00:00:00"

        return MAC

    
    def add_port_listener(self, dpid, port, listener):
        self.port_listeners[dpid][port].append(listener)
        
    def remove_port_listener(self, dpid, port, listener):
        try:
            self.port_listeners[dpid][port].remove(listener)
        except Exception, e: 
            logger.warn('Failed to remove port %d from dpid %d' %(port, dpid))
            pass

    def fire_port_listeners(self, dpid, portno, port):        
        for listener in self.port_listeners[dpid][portno]:
            if not listener(port):
                self.remove_port_listener(dpid, portno, listener)

    def port_timer(self, dp):
        if dp in self.dp_stats:
            self.ctxt.send_port_stats_request(dp, OFPP_NONE)
            self.post_callback(self.dp_poll_period[dp]['port'] + 1, lambda :  self.port_timer(dp))

    def table_timer(self, dp):
        if dp in self.dp_stats:
            self.ctxt.send_table_stats_request(dp)
            self.post_callback(self.dp_poll_period[dp]['table'], lambda : self.table_timer(dp))
       
    def dp_join(self, dp, stats):

        #dpid_obj = datapathid.from_host(dp)
        stats['dpid']     = dp 
        self.dp_stats[dp] = stats
       
        # convert all port hw_addrs to ASCII
        # and register all port names with bindings storage
   
        port_list = self.dp_stats[dp]['ports']
        for i in range(0,len(port_list)):
          new_mac = mac_to_str(port_list[i]['hw_addr']).replace(':','-')
          port_list[i]['hw_addr'] = new_mac 

        # polling intervals for switch statistics
        self.dp_poll_period[dp] = {} 
        self.dp_poll_period[dp]['table'] = DEFAULT_POLL_TABLE_PERIOD
        self.dp_poll_period[dp]['port']  = DEFAULT_POLL_PORT_PERIOD
        self.dp_poll_period[dp]['aggr']  = DEFAULT_POLL_AGGREGATE_PERIOD

        # Switch descriptions do not change while connected, so just send once
        self.ctxt.send_desc_stats_request(dp)
           
        # stagger timers by one second
        # ppershing: I removed unnecessary callbacks to speed up
        # model checking.
        #self.post_callback(self.dp_poll_period[dp]['table'], 
        #                      lambda : self.table_timer(dp))
        #self.post_callback(self.dp_poll_period[dp]['port'] + 1, 
        #                      lambda : self.port_timer(dp))
        return CONTINUE
                
                    
    def dp_leave(self, dp): 
        dpid_obj = datapathid.from_host(dp)

        if self.dp_stats.has_key(dp):
            del self.dp_stats[dp]  
        else:    
            log.err('Unknown datapath leave', system='eate')

        if self.dp_poll_period.has_key(dp):
            del self.dp_poll_period[dp]  
        if self.dp_table_stats.has_key(dp):
            del self.dp_table_stats[dp]  
        if self.dp_desc_stats.has_key(dp):
            del self.dp_desc_stats[dp]  
        if self.dp_port_stats.has_key(dp):
            del self.dp_port_stats[dp]  
        if dp in self.port_listeners:    
            del self.port_listeners[dp]

        return CONTINUE


    def map_name_to_portno(self, dpid, name):
        for port in self.dp_stats[dpid]['ports']:
            if port['name'] == name:
                return port['port_no']
        return None        
            
    def table_stats_in_handler(self, dpid, tables):
##         print "Table stats in from datapath", dpid
##         for item in tables:
##             print '\t',item['name'],':',item['active_count']
        self.dp_table_stats[dpid] = tables

    def desc_stats_in_handler(self, dpid, desc):
##         print "Desc stats in from datapath", dpid

        self.dp_desc_stats[dpid] = desc
        ip = self.ctxt.get_switch_ip(dpid)
        self.dp_desc_stats[dpid]["ip"] = str(create_ipaddr(c_htonl(ip)))


    def port_stats_in_handler(self, dpid, ports):
##         print "Port stats in from datapath", dpid
##         for item in ports:
##             print '\t',item['port_no'],':',item['tx_packets']

        if dpid not in self.dp_port_stats:
            new_ports = {}
            for port in ports:
                port['delta_bytes'] = 0 
                new_ports[port['port_no']] = port
            self.dp_port_stats[dpid] = new_ports 
            return
        new_ports = {}
        for port in ports:    
            if port['port_no'] in self.dp_port_stats[dpid]:
                port['delta_bytes'] = port['tx_bytes'] - \
                            self.dp_port_stats[dpid][port['port_no']]['tx_bytes']
                new_ports[port['port_no']] = port
            else:
                port['delta_bytes'] = 0 
                new_ports[port['port_no']] = port
#             print "Port", port['port_no'], "delta stats in from datapath", port['delta_bytes']
            # XXX Fire listeners for port stats    
            self.fire_port_listeners(dpid, port['port_no'], port)
        self.dp_port_stats[dpid] = new_ports 
        self.energyState(dpid)

    def print_port_statistics(self):
        if self.dp_port_stats.has_key(1) and self.dp_port_stats[1].has_key(2) and  self.dp_port_stats.has_key(2) and self.dp_port_stats[2].has_key(1) and  self.dp_port_stats.has_key(3) and self.dp_port_stats[3].has_key(1) and  self.dp_port_stats.has_key(3) and self.dp_port_stats[3].has_key(2): 
            logger.info('links LtoR %d %d' %
                        (self.dp_port_stats[1][2]['delta_bytes'],
                        self.dp_port_stats[3][2]['delta_bytes']))     
        
            logger.info('links RtoL %d %d' %
                        (self.dp_port_stats[2][1]['delta_bytes'],
                        self.dp_port_stats[3][1]['delta_bytes']))       
        
    def port_status_handler(self, dpid, reason, port):
        intdp = int(dpid)
        if intdp not in self.dp_stats:
            log.err('port status from unknown datapath', system='eate')
            return
        # copy over existing port status
        for i in range(0, len(self.dp_stats[intdp]['ports'])):
            oldport  = self.dp_stats[intdp]['ports'][i]
            if oldport['name'] == port['name']:
                port['hw_addr'] = mac_to_str(port['hw_addr']).replace(':','-')
                self.dp_stats[intdp]['ports'][i] = port

    def get_switch_conn_p_s_heavy_hitters(self):
        hitters = []
#         for dp in self.dp_stats:
#             hitters.append((dp, self.cswitchstats.get_switch_conn_p_s(dp)))
        return hitters

    def get_switch_port_error_heavy_hitters(self): 
        error_list = []
        for dpid in self.dp_port_stats:
            ports = self.dp_port_stats[dpid].values()
            for port in ports:
                error_list.append((dpid, port['port_no'], port['rx_errors'] + port['tx_errors']))
        return error_list    

    def get_switch_port_bandwidth_hitters(self): 
        error_list = []
        for dpid in self.dp_port_stats:
            ports = self.dp_port_stats[dpid].values()
            for port in ports:
                error_list.append((dpid, port['port_no'], 
                  (port['delta_bytes']) / DEFAULT_POLL_PORT_PERIOD))
        return error_list    

    def energyState(self,dpid):
        # had & instead of and
        # the lower if statement for 6 would not fire
        # putting 'and' fixed the bug
        # no checking for self.dp_port_stats[5].has_key(2): can dump?
        if dpid == 1 and self.dp_port_stats.has_key(1) and self.dp_port_stats[1].has_key(2):
#             logger.info('%s energy: %s med %d' %
#                         (dpid, self.dp_port_stats[5][2]['delta_bytes'],
#                          MEDIUM_THRESHOLD))
            if self.dp_port_stats[1][2]['delta_bytes'] > MEDIUM_THRESHOLD:
                inst.energyLtoR = "onDemand"
                if self.dp_port_stats[1][2]['delta_bytes'] > HIGH_THRESHOLD:
                    inst.onDemandLevelLtoR = "high"
                else:
                    inst.onDemandLevelLtoR = "medium"
                logger.info('energy: OnDemand LtoR %s' % inst.onDemandLevelLtoR)
            else:
                inst.energyLtoR = "alwaysOn"
                logger.info('energy: alwaysOn LtoR')

#         if dpid == 5 & self.dp_port_stats.has_key(6):           
        if dpid == 2 and self.dp_port_stats.has_key(2) and self.dp_port_stats[2].has_key(2):           
#             logger.info('%s energy: %s med %d' %
#                         (dpid, self.dp_port_stats[6][2]['delta_bytes'],
#                          MEDIUM_THRESHOLD))
            if self.dp_port_stats[2][1]['delta_bytes'] > MEDIUM_THRESHOLD:
                inst.energyRtoL = "onDemand"
                if self.dp_port_stats[2][1]['delta_bytes'] > HIGH_THRESHOLD:
                    inst.onDemandLevelRtoL = "high"
                else:
                    inst.onDemandLevelRtoL = "medium"
                logger.info('energy: OnDemand RtoL %s' % inst.onDemandLevelLtoR)
            else:
                inst.energyRtoL = "alwaysOn"
                logger.info('energy: alwaysOn RtoL')
        
        if dpid == 2:
            inst.print_port_statistics()
        
    def __init__(self, ctxt):
        global inst
        Component.__init__(self, ctxt)
        self.st = {}
        self.activeSwitches = {}
        self.switches = []
        self.hosts = []
        self.switchPortStat = {}
        self.switchPortMap = {}
        self.alwaysOnMap = {}
        self.onDemandMap = {}
        self.switchPath = {}
        self.onDemandPath = {}
        self.alwaysOnPath = {}
        self.energyLtoR = "alwaysOn"
        self.energyRtoL = "alwaysOn"
        self.onDemandLevelLtoR = "medium"
        self.onDemandLevelRtoL = "medium"
        self.lastSwitchList = []
        
#  from switch statistics

        # {dpid : {port : [listeners]}}
        self.port_listeners = defaultdict(lambda: defaultdict(list)) 

        self.dp_stats = {} 

        self.dp_poll_period = {}
        self.dp_table_stats = {}
        self.dp_desc_stats = {}
        self.dp_port_stats  = {}
        
        inst = self

    def install(self):
        self.deployRules()
        inst.register_for_packet_in(packet_in_callback)
#         inst.register_for_datapath_leave(datapath_leave_callback)
        inst.register_for_datapath_join(datapath_join_callback)

#  from switch statistics
#         self.cswitchstats     = self.resolve(pycswitchstats)

        self.register_for_datapath_join (self.dp_join)
        #self.register_for_datapath_leave(self.dp_leave)

#  we do not need table and desc statistics right now
#         self.register_for_table_stats_in(self.table_stats_in_handler)
#         self.register_for_desc_stats_in(self.desc_stats_in_handler)
        self.register_for_port_stats_in(self.port_stats_in_handler)
        #self.register_for_port_status(self.port_status_handler)

    def getInterface(self):
        return str(eate)

    def dump_equivalent_state(self):
        """ function added to have a serialized version of the app with only the necessary state """
        import utils
        di = Component.dump_equivalent_state(self)
        di["dp_port_stats"] = utils.copy_state(self.dp_port_stats)
        di["energyLtoR"] = utils.copy_state(self.energyLtoR)
        di["energyRtoL"] = utils.copy_state(self.energyRtoL)
        di["lastSwitchList"] = utils.copy_state(self.lastSwitchList)
        return di

    def custom_copy(self, c, memo):
        c.__dict__["dp_port_stats"] = copy.deepcopy(self.dp_port_stats, memo)
        c.__dict__["energyLtoR"] = copy.deepcopy(self.energyLtoR, memo)
        c.__dict__["energyRtoL"] = copy.deepcopy(self.energyRtoL, memo)
        c.__dict__["lastSwitchList"] = copy.deepcopy(self.lastSwitchList, memo)

    def restore_state(self):
        global inst
        inst = self

def getFactory():
    class Factory:
        def instance(self, ctxt):
            return eate(ctxt)

    return Factory()
