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
    flow[core.DL_DST] = packet.src
    actions = [[openflow.OFPAT_OUTPUT, [0, inport]]]
    inst.install_datapath_flow(dpid, flow, CACHE_TIMEOUT, openflow.OFP_FLOW_PERMANENT, actions,
    None, openflow.OFP_DEFAULT_PRIORITY, inport, None)

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
        inst.st[dpid] = {}

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
        self.st = {}

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
