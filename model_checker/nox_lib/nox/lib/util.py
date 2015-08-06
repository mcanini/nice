#
# Copyright (c) 2011, EPFL (Ecole Politechnique Federale de Lausanne)
# All rights reserved.
#
# Created by Marco Canini, Daniele Venzano, Dejan Kostic, Jennifer Rexford
# This file contains code from the NOX Openflow controller
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

import core
from nox.lib.packet.ipv4 import ipv4
from nox.lib.packet.tcp import tcp

def extract_flow(ethernet):
    """
    Extracts and returns flow attributes from the given 'ethernet' packet.
    The caller is responsible for setting IN_PORT itself.
    """
    attrs = {}
    attrs[core.DL_SRC] = ethernet.src
    attrs[core.DL_DST] = ethernet.dst
    attrs[core.DL_TYPE] = ethernet.type
    p = ethernet.next

    # We do not have VLANs
    attrs[core.DL_VLAN] = 0xffff # FIXME should be written OFP_VLAN_NONE
    attrs[core.DL_VLAN_PCP] = 0

    if isinstance(p, ipv4):
        attrs[core.NW_SRC] = p.srcip
        attrs[core.NW_DST] = p.dstip
        attrs[core.NW_PROTO] = p.protocol
        attrs[core.NW_TOS] = p.tos
        p = p.next

        if isinstance(p, tcp):
            attrs[core.TP_SRC] = p.srcport
            attrs[core.TP_DST] = p.dstport
        else:
            attrs[core.TP_SRC] = 0
            attrs[core.TP_DST] = 0
    else:
        attrs[core.NW_SRC] = 0
        attrs[core.NW_DST] = 0
        attrs[core.NW_PROTO] = 0
        attrs[core.TP_SRC] = 0
        attrs[core.TP_DST] = 0
        attrs[core.NW_TOS] = 0

    return attrs
