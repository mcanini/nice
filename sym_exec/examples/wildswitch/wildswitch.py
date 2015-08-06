# Copyright 2008 (C) Nicira, Inc.
# 
# This file is part of NOX.
# 
# NOX is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# NOX is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with NOX.  If not, see <http://www.gnu.org/licenses/>.
# Python L2 learning switch 
#
# ----------------------------------------------------------------------
#
# This app functions as the control logic of an L2 learning switch for
# all switches in the network. On each new switch join, it creates 
# an L2 MAC cache for that switch. 
#
# In addition to learning, flows are set up in the switch for learned
# destination MAC addresses.  Therefore, in the absence of flow-timeout,
# pyswitch should only see one packet per flow (where flows are
# considered to be unidirectional)
#

from nox.lib.core     import *

from nox.lib.packet.ethernet     import ethernet
from nox.lib.packet.packet_utils import mac_to_str, mac_to_int

from twisted.python import log

import logging
from time import time
from socket import htons
from struct import unpack

logger = logging.getLogger('nox.coreapps.examples.pyswitch')

# Global pyswitch instance 
inst = None

# Timeout for cached MAC entries
CACHE_TIMEOUT = 5


# --
# Given a packet, learn the source and peg to a switch/inport 
# --
def do_l2_learning(dpid, inport, packet, buf, bufid):
    global inst 

    # learn MAC on incoming port
    srcaddr = packet.src.tostring()
    if ord(srcaddr[0]) & 1:
        return
    if inst.st[dpid].has_key(srcaddr):
        dst = inst.st[dpid][srcaddr]
        if dst[0] != inport:
            log.msg('MAC has moved from '+str(dst)+'to'+str(inport), system='pyswitch')
        else:
            return
    else:
        log.msg('learned MAC '+mac_to_str(packet.src)+' on %d %d'% (dpid,inport), system="pyswitch")

    # learn or update timestamp of entry
    inst.st[dpid][srcaddr] = (inport, time(), packet)
    # and set-up wildcard flow to this mac address
    flow = {}
    flow[core.DL_DST] = srcaddr
    actions = [[openflow.OFPAT_OUTPUT, [0, inport]]]
    inst.install_datapath_flow(dpid, flow, CACHE_TIMEOUT, openflow.OFP_FLOW_PERMANENT, actions, bufid, openflow.OFP_DEFAULT_PRIORITY, inport, buf)

# --
# If we've learned the destination MAC set up a flow and
# send only out of its inport.  Else, flood.
# --
def forward_l2_packet(dpid, inport, packet, buf, bufid):    
    dstaddr = packet.dst.tostring()
    if not ord(dstaddr[0]) & 1 and inst.st[dpid].has_key(dstaddr):
        prt = inst.st[dpid][dstaddr]
        if  prt[0] == inport:
            log.err('**warning** learned port = inport', system="pyswitch")
            inst.send_openflow(dpid, bufid, buf, openflow.OFPP_FLOOD, inport)
        else:
            log.msg('**warning** received packet for which destination flow should be set up in the  switch')
            # oops, what to do? We can flood.
            inst.send_openflow(dpid, bufid, buf, openflow.OFPP_FLOOD, inport)
    else:
        # haven't learned destination MAC. Flood 
        inst.send_openflow(dpid, bufid, buf, openflow.OFPP_FLOOD, inport)
        

# --
# Packet entry method.
# Drop LLDP packets (or we get confused) and attempt learning and
# forwarding
# --
def packet_in_callback(dpid, inport, reason, len, bufid, packet):
    if not inst.st.has_key(dpid):
        log.msg('registering new switch %x' % dpid,system='pyswitch')
        inst.st[dpid] = Map()

    # don't forward lldp packets    
    if packet.type == ethernet.LLDP_TYPE:
        return CONTINUE

    # learn MAC on incoming port
    do_l2_learning(dpid, inport, packet, packet.arr, bufid)

    forward_l2_packet(dpid, inport, packet, packet.arr, bufid)

    return CONTINUE

def datapath_join_callback(dpid, stats):
    logger.info('Switch %x has joined the network' % dpid)

class wildswitch(Component):

    def __init__(self, ctxt):
        global inst
        Component.__init__(self, ctxt)
        self.st = Map()

        inst = self

    def install(self):
        inst.register_for_packet_in(packet_in_callback)
        inst.register_for_datapath_join(datapath_join_callback)

    def getInterface(self):
        return str(pyswitch)

def getFactory():
    class Factory:
        def instance(self, ctxt):
            return pyswitch(ctxt)

    return Factory()
