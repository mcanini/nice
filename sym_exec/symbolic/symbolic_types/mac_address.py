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

import symbolic.stp as stp
from symbolic_type import SymbolicType
from integers import SymbolicInteger

class SymbolicMacAddress(SymbolicType):
    def __init__(self, name):
        SymbolicType.__init__(self, name)
        self.stp_var = stp.newMacVariable(self.name)
        self.data = (SymbolicInteger(name+"#mac_byte_5", 8, self.stp_var, 47, 40),
                SymbolicInteger(name+"#mac_byte_4", 8, self.stp_var, 39, 32),
                SymbolicInteger(name+"#mac_byte_3", 8, self.stp_var, 31, 24),
                SymbolicInteger(name+"#mac_byte_2", 8, self.stp_var, 23, 16),
                SymbolicInteger(name+"#mac_byte_1", 8, self.stp_var, 15, 8),
                SymbolicInteger(name+"#mac_byte_0", 8, self.stp_var, 7, 0))
        self._bitlen = 48

    def getBitLength(self):
        return self._bitlen

    def tostring(self):
        return self

    def __getitem__(self, key):
        return self.data[key]

    def __repr__(self):
        s = self.name + "#"
        for i in self.data:
            s += "%02x" % i.getConcrValue() + ":"
        return s[:-1]

    def __hash__(self):
        return hash(self.data)

    def __eq__(self, other):
        if isinstance(other, type(None)):
            return False
        if isinstance(other, SymbolicMacAddress):
            return self.data == other.data
        elif isinstance(other, type(())):
            return self.data == other
        if isinstance(other, long) or isinstance(other, int):
            return long(self) == other
        else:
            raise NotImplementedError

    def __cmp__(self, other):
        if isinstance(other, type(None)):
            return 1
        if isinstance(other, SymbolicMacAddress):
            other = other.data
        if isinstance(other, type(())):
            if len(self.data) < len(other):
                return -1
            elif len(self.data) > len(other):
                return 1
            for i in range(0, 6):
                if self.data[i] > other[i]:
                    return 1
                elif self.data[i] < other[i]:
                    return -1
            return 0
        if isinstance(other, long) or isinstance(other, int):
            return long(self) == other
        else:
            raise NotImplementedError

        return 0

    def getConcrValue(self):
        return (self.data[0].getConcrValue(),
            self.data[1].getConcrValue(),
            self.data[2].getConcrValue(),
            self.data[3].getConcrValue(),
            self.data[4].getConcrValue(),
            self.data[5].getConcrValue())

    def setConcrValue(self, value):
        if isinstance(value, type(())):
            for i in range(0, 6):
                self.data[i].setConcrValue(value[i])
        else:
            aux = (value & 0xFF0000000000) >> 40
            self.data[0].setConcrValue(aux)
            aux = (value & 0x00FF00000000) >> 32
            self.data[1].setConcrValue(aux)
            aux = (value & 0x0000FF000000) >> 24
            self.data[2].setConcrValue(aux)
            aux = (value & 0x000000FF0000) >> 16
            self.data[3].setConcrValue(aux)
            aux = (value & 0x00000000FF00) >> 8
            self.data[4].setConcrValue(aux)
            aux = (value & 0x0000000000FF)
            self.data[5].setConcrValue(aux)

    def __long__(self):
        aux = long(0)
        aux = self.data[0].getConcrValue() << 40
        aux |= self.data[1].getConcrValue() << 32
        aux |= self.data[2].getConcrValue() << 24
        aux |= self.data[3].getConcrValue() << 16
        aux |= self.data[4].getConcrValue() << 8
        aux |= self.data[5].getConcrValue()
        return aux

    def isTerm(self):
        return True

    def getSTPVariable(self):
        return [(self.name, self, self.stp_var)]

    def __getstate__(self):
        filtered_dict = {}
        filtered_dict["data"] = self.getConcrValue()
        return filtered_dict

if __name__ == "__main__":
    a = SymbolicMacAddress("packet0")
    a.data[0].setConcrValue(1)
    a.data[1].setConcrValue(2)
    a.data[2].setConcrValue(3)
    a.data[3].setConcrValue(4)
    a.data[4].setConcrValue(5)
    a.data[5].setConcrValue(6)
    print a
    print long(a) == 0x010203040506

