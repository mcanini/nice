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

class FunctionInvocation:
    def __init__(self, function):
        self.function = function
        self.inputs = {}
        self.symbolic_inputs = {}

    def addParameter(self, param, value):
        """ Add ordinary parameter
        """
        self.inputs[param] = value
    
    def addSymbolicParameter(self, name, symbolic_name, type_ref):
        """ Add symbolic parameter with specified name
        """
        self.symbolic_inputs[name] = type_ref(symbolic_name)

    def setupTracer(self, tracer):
        tracer.setFunction(self.function)
        for name, value in self.inputs.items():
            tracer.addFunParam(name, value)
        for name, value in self.symbolic_inputs.items():
            tracer.addFunParam(name, value)

class NicePacketInInvocation(FunctionInvocation):
    def __init__(self, function):
        FunctionInvocation.__init__(self, function)
        self.state = None

    def setState(self, packet, state):
        self.state = state
        cpkt = self.symbolic_inputs["packet"]
        cpkt.name = packet["name"]
        cpkt.type.setConcrValue(packet["type"])
        cpkt.src.setConcrValue(packet["src"])
        cpkt.dst.setConcrValue(packet["dst"])

class NicePortStatsInInvocation(FunctionInvocation):
    def __init__(self, function):
        FunctionInvocation.__init__(self, function)
        self.state = None

    def setState(self, data, state):
        self.state = state
        pass
