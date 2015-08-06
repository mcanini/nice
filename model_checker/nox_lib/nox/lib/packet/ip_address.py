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

import struct
import utils

class IpAddress:
    def __init__(self, value=(0, 0, 0, 0)):
        if isinstance(value, IpAddress):
            value = value.data[:]
        elif isinstance(value, type(())):
            value = value[:]
        elif isinstance(value, str):
            value = value.split(".")
            value = map(lambda x: int(x), value)
            value = tuple(value)
        else:
            utils.crash("Creating an IpAddress from something unknown")
        self.data = value

    def tostring(self):
        return struct.pack("BBBB", *self.data)

    def toint(self):
        return self.data[0] << 24 | self.data[1] << 16 | self.data[2] <<  8 | self.data[3]

    def __iter__(self):
        return self.data.__iter__()

    def __repr__(self):
        s = "%d.%d.%d.%d" % self.data
        return s

    def __eq__(self, other):
        if isinstance(other, int):
            return self.toint() == other
        elif isinstance(other, IpAddress):
            return self.data == other.data
        else:
            raise NotImplementedError

    def __ne__(self, other):
        if isinstance(other, int):
            return self.toint() != other
        elif isinstance(other, IpAddress):
            return self.data != other.data
        else:
            raise NotImplementedError

    def __lt__(self, other):
        if isinstance(other, IpAddress):
            return self.data < other.data
        elif isinstance(other, int):
            return self.toint() < other
        else:
            raise NotImplementedError

    def __hash__(self):
        return hash(self.data)

    def __rshift__(self, other):
        return self.toint() >> other

    def __and__(self, other):
        return self.toint() & other

    def __mod__(self, other):
        return self.toint() % other

    def copy(self):
        return IpAddress(self.data)

    def dump_equivalent_state(self):
        return repr(self)

