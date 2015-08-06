#
# Copyright (c) 2011, EPFL (Ecole Politechnique Federale de Lausanne)
# All rights reserved.
#
# Created by Marco Canini, Daniele Venzano, Dejan Kostic, Jennifer Rexford
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

# Possible values for the "reason" parameter
OFPR_NO_MATCH = 0 # No matching flow
OFPR_ACTION = 1 # Explicitly output to controller

# Maximum number of physical switch ports
OFPP_MAX = 0xff00

# Fake output "ports"
OFPP_IN_PORT = 0xfff8
OFPP_TABLE = 0xfff9
OFPP_NORMAL = 0xfffa
OFPP_FLOOD = 0xfffb
OFPP_ALL = 0xfffc
OFPP_CONTROLLER = 0xfffd
OFPP_LOCAL = 0xfffe
OFPP_ANY = 0xffff
OFPP_NONE = OFPP_ANY # was renamed in NOX

OFP_FLOW_PERMANENT = 0
OFP_DEFAULT_PRIORITY = 32768

# Actions
OFPAT_OUTPUT = 0
OFPAT_SET_VLAN_VID = 1
OFPAT_SET_VLAN_PCP = 2
OFPAT_STRIP_VLAN = 3
OFPAT_SET_DL_SRC = 4
OFPAT_SET_DL_DST = 5
OFPAT_SET_NW_SRC = 6
OFPAT_SET_NW_DST = 7
OFPAT_SET_NW_TOS = 8
OFPAT_SET_TP_SRC = 9
OFPAT_SET_TP_DST = 10
OFPAT_ENQUEUE = 11
OFPAT_VENDOR = 65535

# Flow table modification messages
OFPFC_ADD = 0
OFPFC_MODIFY = 1
OFPFC_MODIFY_STRICT = 2
OFPFC_DELETE = 3
OFPFC_DELETE_STRICT = 4

# Port configuration
OFPPC_PORT_DOWN = 1 << 0
OFPPC_NO_STP =    1 << 1
OFPPC_NO_RECV =   1 << 2
OFPPC_NO_RECV_STP = 1 << 3
OFPPC_NO_FLOOD =  1 << 4
OFPPC_NO_FWD =    1 << 5
OFPPC_NO_PACKET_IN = 1 << 6

# Port status
OFPPS_LINK_DOWN =  1 << 0
OFPPS_STP_LISTEN = 0 << 8
OFPPS_STP_LEARN =  1 << 8
OFPPS_STP_FORWARD = 2 << 8
OFPPS_STP_BLOCK =  3 << 8
OFPPS_STP_MASK =   4 << 8

# Port reasons
OFPPR_ADD = 0
OFPPR_DELETE = 1
OFPPR_MODIFY = 2

# Flow removed reasons
OFPRR_IDLE_TIMEOUT = 0
OFPRR_HARD_TIMEOUT = 1
OFPRR_DELETE = 2
OFPRR_GROUP_DELETE = 3

# Match wildcards
OFPFW_IN_PORT  = 1 << 0
OFPFW_DL_VLAN  = 1 << 1
OFPFW_DL_SRC   = 1 << 2
OFPFW_DL_DST   = 1 << 3
OFPFW_DL_TYPE  = 1 << 4
OFPFW_NW_PROTO = 1 << 5
OFPFW_TP_SRC   = 1 << 6
OFPFW_TP_DST   = 1 << 7 

OFPFW_NW_SRC_SHIFT = 8
OFPFW_NW_SRC_BITS = 6
OFPFW_NW_SRC_MASK = ((1 << OFPFW_NW_SRC_BITS) - 1) << OFPFW_NW_SRC_SHIFT
OFPFW_NW_SRC_ALL = 32 << OFPFW_NW_SRC_SHIFT

OFPFW_NW_DST_SHIFT = 14
OFPFW_NW_DST_BITS = 6
OFPFW_NW_DST_MASK = ((1 << OFPFW_NW_DST_BITS) - 1) << OFPFW_NW_DST_SHIFT
OFPFW_NW_DST_ALL = 32 << OFPFW_NW_DST_SHIFT

OFPFW_DL_VLAN_PCP = 1 << 20
OFPFW_NW_TOS = 1 << 21

OFPFW_ALL = ((1 << 22) - 1)

class OfpFlowRemoved:
    def __init__(self):
        self.priority = 0
        self.reason = OFPRR_DELETE
        self.table_id = 0
        self.duration_sec = 0
        self.duration_nsec = 0
        self.idle_timeout = 0
        self.packet_count = 0
        self.byte_count = 0
        self.match = None

    def __eq__(self, other):
        eq = True
        eq = eq and self.priority == other.priority
        eq = eq and self.reason == other.reason
        eq = eq and self.table_id == other.table_id
        eq = eq and self.duration_sec == other.duration_sec
        eq = eq and self.duration_nsec == other.duration_nsec
        eq = eq and self.idle_timeout == other.idle_timeout
        eq = eq and self.packet_count == other.packet_count
        eq = eq and self.byte_count == other.byte_count
        eq = eq and self.match == other.match
        return eq

    def __ne__(self, other):
        return not self.__eq__(other)

