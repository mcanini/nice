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

import pydot

class ModelCheckingGraph:
    def __init__(self, fname, mc):
        self.dot_graph = pydot.Graph(graph_name="MC", graph_type="digraph",
            simplify=True, rankdir="LR")
        self.node_cache = {}
        self.node_count = 0
        self.current_transition = None
        self.fname = fname
        self.mc = mc

    def getNode(self, name):
        if name not in self.node_cache:
            self.node_count = self.node_count + 1
            self.node_cache[name] = pydot.Node(name, label='s%d' % self.node_count)
            self.dot_graph.add_node(self.node_cache[name])
        return self.node_cache[name]

    def getStateName(self, state):
        name = 'state%s' % hash(state)
        return name

    def startTransition(self, state):
        assert self.current_transition == None
        self.current_transition = self.getStateName(state)

    def endTransition(self, state, text):
        assert self.current_transition is not None
        text = text.replace(":", "-")
        s1 = self.current_transition
        s2 = self.getStateName(state)
        self.getNode(s1)
        self.getNode(s2)
        self.addEdge(s1, s2, text)
        self.current_transition = None

    def addEdge(self, nodename1, nodename2, text):
        edge = pydot.Edge(nodename1, nodename2, label=text)
        self.dot_graph.add_edge(edge)
        return edge

    def saveToFile(self):
        f = open(self.fname, "w")
        f.write(self.dot_graph.to_string())

