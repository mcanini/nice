#
# This file is part of Nice, a NICE way to test OpenFlow controller applications
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

class Invariant:
    def __init__(self, name):
        self.name = name

    def updateDispatcher(self, dis):
        self.dispatcher = dis

    def reportViolation(self, violation):
        return self.dispatcher.reportViolation(violation)

    def transition_start_cb(self, model):
        pass

    def transition_end_cb(self, model):
        pass

    def path_start_cb(self, model):
        pass

    def path_end_cb(self, model, cached_state):
        pass

    def packet_received_cb(self, model, receiver, packet, port):
        pass

    def packet_sent_cb(self, model, sender, receiver, packet):
        pass

    def before_cnt_packet_in_cb(self, model, buffer_id, packet, inport, reason, dp_id):
        pass

    def after_cnt_packet_in_cb(self, model, controller, packet, return_value, dp_id):
        pass

    def switch_flood_packet_start_cb(self, model, switch, packet):
        pass

    def switch_sent_packet_on_port_cb(self, model, switch, packet, port):
        pass

    def switch_enqueue_command_cb(self, model, switch, command):
        pass

    def switch_process_packet_cb(self, model, switch, packet, port):
        pass

    def syn_packet_received_cb(self, model, receiver, packet):
        pass

    def ack_packet_received_cb(self, model, receiver, packet):
        pass

    def tcp_connection_start_cb(self, model, client, packet):
        pass

    def dump_equivalent_state(self):
        return None

