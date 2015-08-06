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

import utils

class Action:
    def __init__(self, node_name, target, args):
        self.node_name = node_name
        self.target = target
        self.args = args
        self.priority = None
    
    def __eq__(self, other):
        return self.node_name == other.node_name and self.target == other.target and \
            self.args == other.args
    
    def __lt__(self, other):
        if self.node_name == other.node_name:
            if self.target == other.target:
                return self.args < other.args
            else:
                return self.target < other.target
        else:
            return self.node_name < other.node_name

    def __repr__(self):
        s = self.node_name + "." + self.target + "("
        for a in self.args:
            if isinstance(a, list) or isinstance(a, dict):
                s += "..., "
            else:
                s += str(a) + ", "
        s += ")"
        return s
    
    def __hash__(self):
        """Needed by DPOR """
        h = hash(self.node_name + "." + self.target + str(self.args))
        return h

    def dump_equivalent_state(self):
        filtered_dict = {}
        filtered_dict["node_name"] = utils.copy_state(self.node_name)
        filtered_dict["target"] = utils.copy_state(self.target)
        filtered_dict["args"] = utils.copy_state(self.args)
        return filtered_dict

