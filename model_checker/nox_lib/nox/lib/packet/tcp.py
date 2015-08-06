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

from packet_base import packet_base
import utils

class tcp(packet_base):
    FIN  = 0x01
    SYN  = 0x02
    RST  = 0x04
    PUSH = 0x08
    ACK  = 0x10
    URG  = 0x20
    ECN  = 0x40
    CWR  = 0x80

    def __init__(self):
        self.srcport  = 0 # 16 bit
        self.dstport  = 0 # 16 bit
        self.seq      = 0 # 32 bit
        self.ack      = 0 # 32 bit
        self.off      = 0 # 4 bits
        self.res      = 0 # 4 bits
        self.flags    = 0 # reserved, 2 bits flags 6 bits
        self.win      = 0 # 16 bits
        self.csum     = 0 # 16 bits
        self.urg      = 0 # 16 bits
        self.tcplen   = 20 # Options? 
        self.options  = []  
        self.flow_id = None # Not part of the TCP header, used to track flows in invariants

    def copy(self):
        cpy = tcp()
        cpy.srcport = self.srcport
        cpy.dstport = self.dstport
        cpy.seq = self.seq  
        cpy.ack = self.ack  
        cpy.off = self.off  
        cpy.res = self.res  
        cpy.flags = self.flags  
        cpy.win = self.win  
        cpy.csum = self.csum    
        cpy.urg = self.urg  
        cpy.tcplen = self.tcplen 
        cpy.options = self.options[:]
        cpy.flow_id = self.flow_id
        if self.next != None:
            cpy.set_payload(self.next.copy())
        return cpy

    def __repr__(self):
        return "tcp: " + str((self.srcport, self.dstport, "0x%x" % self.flags, self.flow_id))

    def dump_equivalent_state(self):
        filtered_dict = packet_base.dump_equivalent_state(self)
        filtered_dict["srcport"] = utils.copy_state(self.srcport)
        filtered_dict["dstport"] = utils.copy_state(self.dstport)
        filtered_dict["seq"] = utils.copy_state(self.seq)
        filtered_dict["ack"] = utils.copy_state(self.ack)
        filtered_dict["off"] = utils.copy_state(self.off)
        filtered_dict["res"] = utils.copy_state(self.res)
        filtered_dict["flags"] = utils.copy_state(self.flags)
        filtered_dict["win"] = utils.copy_state(self.win)
        filtered_dict["csum"] = utils.copy_state(self.csum)
        filtered_dict["urg"] = utils.copy_state(self.urg)
        filtered_dict["tcplen"] = utils.copy_state(self.tcplen)
        filtered_dict["options"] = utils.copy_state(self.options)
        return filtered_dict

    def toScapy(self):
        from scapy.layers.inet import TCP

        sport = self.srcport
        dport = self.dstport
        seq = self.seq
        ack = self.ack
        dataofs = self.off
        reserved = self.res
        flags = self.flags
        window = self.win
        chksum = self.csum          ##
        urgptr = self.urg
        options = self.options[:]   # dict required?
        #no flow_id

        p = TCP(sport = sport, dport = dport, seq = seq, ack = ack, reserved = reserved, flags = flags, window = window, urgptr = urgptr)

        if self.next == None:
            return p, None
        elif isinstance(self.next, packet_base):
            p2, data = self.next.toScapy()
            return p/p2, data
        elif isinstance(self.next, str):
            return p, self.next



