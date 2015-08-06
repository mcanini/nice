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

from symbolic.symbolic_types import SymbolicMacAddress, SymbolicInteger, SymbolicType

class ethernet:
    IP_TYPE = 2048
    ARP_TYPE = 2054
    RARP_TYPE = 32821
    VLAN_TYPE = 33024
    LLDP_TYPE = 35020
    PAE_TYPE = 34958

    def __init__(self, name):
        """ name is the name of ethernet symbolic variable """
        self.name = name
        self.parsed = True
        self.src = SymbolicMacAddress(name + "#src")
        self.dst = SymbolicMacAddress(name + "#dst")
        self.type = SymbolicInteger(name + "#packet_type", 16)
        self.arr = None
        self.next = None

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return self.name + "(src=" + str(self.src) + ", dst=" + str(self.dst) + ", type=" + str(self.type) + ")"

    def __ne__(self, other):
        if not isinstance(other, ethernet):
            return True
        else:
            raise NotImplementedError

    def __eq__(self, other):
        if not isinstance(other, ethernet):
            return False
        else:
            raise NotImplementedError

    def __getstate__(self):
        filtered_dict = {}
        filtered_dict["name"] = self.name
        filtered_dict["src"] = self.src.__getstate__()
        filtered_dict["dst"] = self.dst.__getstate__()
        filtered_dict["type"] = self.type.__getstate__()
        return filtered_dict

    def getConcrValue(self):
        dd = dict()
        for k in self.__dict__:
            if isinstance(self.__dict__[k], SymbolicType):
                dd[k] = self.__dict__[k].getConcrValue()
            else:
                dd[k] = self.__dict__[k]
        return dd

