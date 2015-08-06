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

from invariant import Invariant
from violation import Violation

from lib.of_flow_table_modification_message import FlowTableModificationMessage
from lib.of_packet_out_message import PacketOutMessage

class NoTruncate(Invariant):
    def __init__(self):
        Invariant.__init__(self, "NoTruncate")

    def path_start_cb(self, model):
        self.bufid = None
        self.packetname = None

    def before_cnt_packet_in_cb(self, model, buffer_id, packet, inport, reason, dp_id):
        self.bufid = buffer_id
        self.packetname = packet.name

    def after_cnt_packet_in_cb(self, model, controller, packet, return_value, dp_id):
        self.bufid = None

    def switch_enqueue_command_cb(self, model, switch, command):
        if isinstance(command, FlowTableModificationMessage) or isinstance(command, PacketOutMessage):
            if command.packet is not None and \
                    self.packetname == command.packet.name and \
                    command.buffer_id != self.bufid:
                v = Violation(self, "Truncated packet " + str(command.packet))
                self.reportViolation(v)

