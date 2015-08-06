import nox.lib.core as core
import nox.lib.openflow as openflow
from nox.lib.packet.mac_address import MacAddress
from nox.lib.packet.ip_address import IpAddress
from nox.lib.packet import ethernet

from oftest.cstruct import *


def createTestPacket():
    eth = ethernet.ethernet("test")
    eth.packet_id = 0
    eth.type = 0x05ff
    eth.src = "55:55:55:55:55:55"
    return eth

def createTestPacketIn():
    eth = ethernet.ethernet("test_in")
    eth.packet_id = 0
    eth.type = 0x05ff
    eth.src = "88:88:88:88:88:88"
    return eth

def createBarrierPacket():
    eth = ethernet.ethernet("barrier_test")
    eth.packet_id = 0
    eth.type = 0x05ff
    eth.src = "66:66:66:66:66:66"
    return eth

def createScapyPacket(packet):
    if packet is None:
        return ""
    p, data = packet.toScapy()
    p = p/data if data is not None else p
    return p

def createMatch(attrs):
    m = ofp_match()
    wildcards = 0
    num_entries = 0

    if attrs.has_key(core.IN_PORT):
        m.in_port = attrs[core.IN_PORT]
        num_entries += 1
    else:
        wildcards = wildcards | openflow.OFPFW_IN_PORT

    if attrs.has_key(core.DL_VLAN):
        m.dl_vlan = attrs[core.DL_VLAN]
        num_entries += 1
    else:
        wildcards = wildcards | openflow.OFPFW_DL_VLAN

    if attrs.has_key(core.DL_VLAN_PCP):
        m.dl_vlan_pcp = attrs[core.DL_VLAN_PCP]
        num_entries += 1
    else:
        wildcards = wildcards | openflow.OFPFW_DL_VLAN_PCP

    if attrs.has_key(core.DL_SRC):
        v = MacAddress(attrs[core.DL_SRC])
        for i in range(0,6):
            m.dl_src[i] = v.data[i]
        num_entries += 1
    else:
        wildcards = wildcards | openflow.OFPFW_DL_SRC

    if attrs.has_key(core.DL_DST):
        v = MacAddress(attrs[core.DL_DST])
        for i in range(0,6):
            m.dl_dst[i] = v.data[i]
        num_entries += 1
    else:
        wildcards = wildcards | openflow.OFPFW_DL_DST

    if attrs.has_key(core.DL_TYPE):
        m.dl_type = attrs[core.DL_TYPE]
        num_entries += 1
    else:
        wildcards = wildcards | openflow.OFPFW_DL_TYPE

    if attrs.has_key(core.NW_SRC):
        if isinstance(attrs[core.NW_SRC], int):
            m.nw_src = attrs[core.NW_SRC]
        else:
            v= IpAddress(attrs[core.NW_SRC])
            m.nw_src = v.toint()
        num_entries += 1

        if attrs.has_key(core.NW_SRC_N_WILD):
            n_wild = attrs[core.NW_SRC_N_WILD]
            if n_wild > 31:
                wildcards |= openflow.OFPFW_NW_SRC_MASK
            elif n_wild >= 0:
                wildcards |= n_wild << openflow.OFPFW_NW_SRC_SHIFT
            else:
                return None
            num_entries += 1
    else:
        wildcards = wildcards | openflow.OFPFW_NW_SRC_MASK

    if attrs.has_key(core.NW_DST):
        if isinstance(attrs[core.NW_DST], int):
            m.nw_dst = attrs[core.NW_DST]
        else:
            v= IpAddress(attrs[core.NW_DST])
            m.nw_dst = v.toint()
        num_entries += 1

        if attrs.has_key(core.NW_DST_N_WILD):
            n_wild = attrs[core.NW_DST_N_WILD]
            if n_wild > 31:
                wildcards |= openflow.OFPFW_NW_DST_MASK
            elif n_wild >= 0:
                wildcards |= n_wild << openflow.OFPFW_NW_DST_SHIFT
            else:
                return None
            num_entries += 1
    else:
        wildcards = wildcards | openflow.OFPFW_NW_DST_MASK

    if attrs.has_key(core.NW_PROTO):
        m.nw_proto = attrs[core.NW_PROTO]
        num_entries += 1
    else:
        wildcards = wildcards | openflow.OFPFW_NW_PROTO

    if attrs.has_key(core.TP_SRC):
        m.tp_src = attrs[core.TP_SRC]
        num_entries += 1
    else:
        wildcards = wildcards | openflow.OFPFW_TP_SRC

    if attrs.has_key(core.TP_DST):
        m.tp_dst = attrs[core.TP_DST]
        num_entries += 1
    else:
        wildcards = wildcards | openflow.OFPFW_TP_DST

    if attrs.has_key(core.NW_TOS):
        m.nw_tos = attrs[core.NW_TOS]
        num_entries += 1
    else:
        wildcards = wildcards | openflow.OFPFW_NW_TOS

    m.wildcards = wildcards
#   print m.show()
    return m

