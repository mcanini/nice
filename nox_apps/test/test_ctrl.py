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
from nox.lib.util     import *

from nox.lib.packet.ethernet     import ethernet
from nox.lib.packet.packet_utils import mac_to_str, mac_to_int
from nox.lib.packet.mac_address import MacAddress
from nox.lib.packet.ip_address import IpAddress
from nox.lib.packet import arp, ethernet, ipv4, tcp

from twisted.python import log

import logging
from time import time
from socket import htons
from struct import unpack

logger = logging.getLogger('nox.coreapps.examples.pyswitch')

# Global pyswitch instance 
inst = None
     

def test1(dpid, inport, reason, len, bufid, packet):
    flow = {} #extract_flow(packet)
    #flow[core.IN_PORT] = inport
    flow[core.DL_SRC] = MacAddress((0x00, 0x00, 0x00, 0x00, 0x01, 0x00))
    flow[core.NW_SRC] = IpAddress("128.0.0.11")
    flow[core.DL_TYPE] = 2048
    actions = [[openflow.OFPAT_OUTPUT, [0, 1]]]

    flow1 = {}
    flow1[core.DL_SRC] = MacAddress((0x00, 0x00, 0x00, 0x00, 0x01, 0x00))
    flow1[core.NW_DST] = IpAddress("128.0.0.12")
    flow1[core.NW_SRC] = IpAddress("128.0.0.11")
    flow1[core.DL_TYPE] = 2048
    actions1 = [] #[[openflow.OFPAT_OUTPUT, [0, 0]]]
    #inst.install_datapath_flow(dpid, flow1, openflow.OFP_FLOW_PERMANENT, openflow.OFP_FLOW_PERMANENT, actions1, None, 1000, inport, packet.arr)
    inst.install_datapath_flow(dpid, flow, openflow.OFP_FLOW_PERMANENT, openflow.OFP_FLOW_PERMANENT, actions, None, 500, inport, packet.arr)

    inst.install_datapath_flow(dpid, {core.DL_TYPE : 2048, core.NW_DST : IpAddress("128.0.0.17")} , openflow.OFP_FLOW_PERMANENT, openflow.OFP_FLOW_PERMANENT, actions, None, 500, inport, packet.arr)
    inst.install_datapath_flow(dpid, {core.DL_TYPE : 2048, core.NW_DST : IpAddress("128.0.0.18")} , openflow.OFP_FLOW_PERMANENT, openflow.OFP_FLOW_PERMANENT, actions, None, 500, inport, packet.arr)
    inst.install_datapath_flow(dpid, {core.DL_TYPE : 2048, core.NW_DST : IpAddress("128.0.0.19")} , openflow.OFP_FLOW_PERMANENT, openflow.OFP_FLOW_PERMANENT, actions, None, 500, inport, packet.arr)
    inst.install_datapath_flow(dpid, {core.DL_TYPE : 2048, core.NW_DST : IpAddress("128.0.0.20")} , openflow.OFP_FLOW_PERMANENT, openflow.OFP_FLOW_PERMANENT, actions, None, 500, inport, packet.arr)
    inst.install_datapath_flow(dpid, {core.DL_TYPE : 2048, core.NW_DST : IpAddress("128.0.0.21")} , openflow.OFP_FLOW_PERMANENT, openflow.OFP_FLOW_PERMANENT, actions, None, 500, inport, packet.arr)
    inst.install_datapath_flow(dpid, {core.DL_TYPE : 2048, core.NW_DST : IpAddress("128.0.0.22")} , openflow.OFP_FLOW_PERMANENT, openflow.OFP_FLOW_PERMANENT, actions, None, 500, inport, packet.arr)
    inst.install_datapath_flow(dpid, {core.DL_TYPE : 2048, core.NW_DST : IpAddress("128.0.0.23")} , openflow.OFP_FLOW_PERMANENT, openflow.OFP_FLOW_PERMANENT, actions, None, 500, inport, packet.arr)
    inst.install_datapath_flow(dpid, {core.DL_TYPE : 2048, core.NW_DST : IpAddress("128.0.0.24")} , openflow.OFP_FLOW_PERMANENT, openflow.OFP_FLOW_PERMANENT, actions, None, 500, inport, packet.arr)

def test2(dpid, inport, reason, len, bufid, packet):
    flow = {}
    flow[core.DL_TYPE] = 2048
    flow[core.NW_SRC] = IpAddress("128.0.0.0")
    flow[core.NW_SRC_N_WILD] = 16
    actions = [[openflow.OFPAT_OUTPUT, [0, 1]]]
    inst.install_datapath_flow(dpid, flow, openflow.OFP_FLOW_PERMANENT, openflow.OFP_FLOW_PERMANENT, actions, None, 500, inport, packet.arr)

def test3(dpid, inport, reason, len, bufid, packet):
    flow = {} #extract_flow(packet)
    #flow[core.IN_PORT] = inport
    flow[core.DL_SRC] = MacAddress((0x00, 0x00, 0x00, 0x00, 0x01, 0x00))
    flow[core.NW_SRC] = IpAddress("128.0.0.11")
    flow[core.DL_TYPE] = 2048
    actions = [[openflow.OFPAT_OUTPUT, [0, 1]]]

    flow1 = {}
    flow1[core.DL_SRC] = MacAddress((0x00, 0x00, 0x00, 0x00, 0x01, 0x00))
    flow1[core.NW_DST] = IpAddress("128.0.0.12")
    flow1[core.NW_SRC] = IpAddress("128.0.0.11")
    flow1[core.DL_TYPE] = 2048
    actions1 = [] #[[openflow.OFPAT_OUTPUT, [0, 0]]]
    #inst.install_datapath_flow(dpid, flow1, openflow.OFP_FLOW_PERMANENT, openflow.OFP_FLOW_PERMANENT, actions1, None, 1000, inport, packet.arr)
    inst.install_datapath_flow(dpid, flow, openflow.OFP_FLOW_PERMANENT, openflow.OFP_FLOW_PERMANENT, actions, None, 500, inport, packet.arr)

    inst.install_datapath_flow(dpid, {core.DL_TYPE : 2048, core.NW_DST : IpAddress("128.0.0.17"), core.NW_TOS : 0} , openflow.OFP_FLOW_PERMANENT, openflow.OFP_FLOW_PERMANENT, actions, None, 500, inport, packet.arr)
    inst.install_datapath_flow(dpid, {core.DL_TYPE : 2048, core.NW_DST : IpAddress("128.0.0.18"), core.NW_TOS : 0} , openflow.OFP_FLOW_PERMANENT, openflow.OFP_FLOW_PERMANENT, actions, None, 500, inport, packet.arr)
    inst.install_datapath_flow(dpid, {core.DL_TYPE : 2048, core.NW_DST : IpAddress("128.0.0.19"), core.NW_TOS : 0} , openflow.OFP_FLOW_PERMANENT, openflow.OFP_FLOW_PERMANENT, actions, None, 500, inport, packet.arr)
    inst.install_datapath_flow(dpid, {core.DL_TYPE : 2048, core.NW_DST : IpAddress("128.0.0.20"), core.NW_TOS : 0} , openflow.OFP_FLOW_PERMANENT, openflow.OFP_FLOW_PERMANENT, actions, None, 500, inport, packet.arr)
    inst.install_datapath_flow(dpid, {core.DL_TYPE : 2048, core.NW_DST : IpAddress("128.0.0.21"), core.NW_TOS : 0} , openflow.OFP_FLOW_PERMANENT, openflow.OFP_FLOW_PERMANENT, actions, None, 500, inport, packet.arr)
    inst.install_datapath_flow(dpid, {core.DL_TYPE : 2048, core.NW_DST : IpAddress("128.0.0.22"), core.NW_TOS : 0} , openflow.OFP_FLOW_PERMANENT, openflow.OFP_FLOW_PERMANENT, actions, None, 500, inport, packet.arr)
    inst.install_datapath_flow(dpid, {core.DL_TYPE : 2048, core.NW_DST : IpAddress("128.0.0.23"), core.NW_TOS : 0} , openflow.OFP_FLOW_PERMANENT, openflow.OFP_FLOW_PERMANENT, actions, None, 500, inport, packet.arr)
    inst.install_datapath_flow(dpid, {core.DL_TYPE : 2048, core.NW_DST : IpAddress("128.0.0.24"), core.NW_TOS : 0} , openflow.OFP_FLOW_PERMANENT, openflow.OFP_FLOW_PERMANENT, actions, None, 500, inport, packet.arr)

def packet_in_callback(dpid, inport, reason, len, bufid, packet):
    test3(dpid, inport, reason, len, bufid, packet)
    
    return CONTINUE

class testCtrl(Component):

    def __init__(self, ctxt):
        global inst
        Component.__init__(self, ctxt)
        self.st = {}

        inst = self

    def install(self):
        inst.register_for_packet_in(packet_in_callback)

    def getInterface(self):
        return str(testCtrl)

    def __getstate__(self):
        """ function added to have a serialized version of the app with only the necessary state """
        di = Component.__getstate__(self)
        di["st"] = {}
        dpids = self.st.keys()
        dpids.sort()
        for d in dpids:
            di["st"][d] = {}
            macs = self.st[d].keys()
            macs.sort()
            for m in macs:
                di["st"][d][m] = (self.st[d][m][0], 0, self.st[d][m][2])
        return di

def getFactory():
    class Factory:
        def instance(self, ctxt):
            return testCtrl(ctxt)

    return Factory()
