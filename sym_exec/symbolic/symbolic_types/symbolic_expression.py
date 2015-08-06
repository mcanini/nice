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

from symbolic_type import SymbolicType
import ast
import utils

class SymbolicExpression(SymbolicType):
    def __init__(self, expr):
        SymbolicType.__init__(self, "se")
        self.expr = expr
        self.concrete_value = None
        self._bitlen = None

    def getExprConcr(self):
        return (self.expr, self.concrete_value)

    def getBitLength(self):
        if self._bitlen == None:
            self._bitlen = self._findBitLength(self.expr)
        return self._bitlen

    def _findBitLength(self, expr):
        if isinstance(expr, ast.BinOp):
            l = self._findBitLength(expr.left)
            r = self._findBitLength(expr.right)
            if l > r:
                return l
            else:
                return r
        elif isinstance(expr, SymbolicType):
            return expr.getBitLength()
        elif isinstance(expr, int) or isinstance(expr, long):
            return 0
        else:
            utils.crash("Node type not supported: %s" % expr)

    def getSTPVariable(self):
        return self._getSTPVariables(self.expr)

    def _getSTPVariables(self, expr):
        stp_vars = []
        if isinstance(expr, ast.BinOp):
            stp_vars += self._getSTPVariables(expr.left)
            stp_vars += self._getSTPVariables(expr.right)
        elif isinstance(expr, SymbolicType):
            stp_vars += expr.getSTPVariable()
        elif isinstance(expr, int) or isinstance(expr, long):
            pass
        else:
            utils.crash("Node type not supported: %s" % expr)

        return stp_vars

    def symbolicEq(self, other):
        if not isinstance(other, SymbolicExpression):
            return False
        return self._do_symbolicEq(self.expr, other.expr)

    def _do_symbolicEq(self, expr1, expr2):
        if type(expr1) != type(expr2):
            return False
        if isinstance(expr1, ast.BinOp):
            ret = self._do_symbolicEq(expr1.left, expr2.left)
            ret |= self._do_symbolicEq(expr1.right, expr2.right)
            return ret | (type(expr1.op) == type(expr2.op))
        elif isinstance(expr1, SymbolicType):
            return expr1 is expr2
        elif isinstance(expr1, int) or isinstance(expr1, long):
            return expr1 == expr2
        else:
            utils.crash("Node type not supported: %s" % expr1)

    def __repr__(self):
        return "SymExpr(" + ast.dump(self.expr) + ")"

if __name__ == "__main__":
    e = SymbolicExpression(None)
    e.concrete_value = 0
    if e:
        print "true"
    else:
        print "false"

