#
# Copyright (c) 2011, EPFL (Ecole Politechnique Federale de Lausanne)
# All rights reserved.
#
# Created by Marco Canini, Daniele Venzano, Dejan Kostic, Jennifer Rexford
# Contributed to this file: Peter Peresini
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

from nox.lib.core import *
from nox.lib.util import *
from nox.lib.packet.ethernet import ethernet

from invariant import Invariant
from violation import Violation

import utils

class EateRouteInvariant(Invariant):
    def __init__(self):
        Invariant.__init__(self, "EateRoute")
        self.packet_balance = 0

    def after_cnt_packet_in_cb(self, model, controller, packet, return_value, dp_id):
        if packet.type != ethernet.IP_TYPE:
            return
        dstip = packet.next.dstip
        srcip = packet.next.srcip

        #route = controller.energyLtoR
        route = controller.choose_path(srcip,dstip)
        if route == "alwaysOn" and srcip.data==(10, 0, 0, 11) and\
            len(controller.lastSwitchList)>0 and controller.lastSwitchList!=[1, 2]:
            v = Violation(self, "wrong alwaysOn route")
            self.reportViolation(v)
        if route == "onDemand" and srcip.data==(10, 0, 0, 11) and\
            len(controller.lastSwitchList)>0 and controller.lastSwitchList!=[1, 3, 2]:
            v = Violation(self, "wrong onDemand route")
            self.reportViolation(v)

    def dump_equivalent_state(self):
        filtered_dict = {}
        filtered_dict["balance"] = utils.copy_state(self.packet_balance)
        return filtered_dict
