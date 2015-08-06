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

import symbolic.stp as stp_mod
import bytecode_opcodes as bc
from symbolic_types import SymbolicExpression

import logging
log = logging.getLogger("nice.se")
import utils

class Predicate:
    """Predicate is one specific ``if'' encountered during the program execution.
       """

    def __init__(self, stmt, result):
        """stmt is statement under consideration
            next_opcode_id is used to determine branch taken
            """
        self.stmt = stmt
        self.result = result
        self.stp_variables = {}

    def __eq__(self, other):
        """ Two Predicates are equal iff
            the have the same statement, same symbolic variables
            and same result
        """
        if isinstance(other, Predicate):
            # it is a different bytecode instruction
            if self.stmt.opcode_id != other.stmt.opcode_id:
                return False
            # different result
            if self.result != other.result:
                return False
            # different variables (i.e. another invocation of function for example)
            my_vars = self.stmt.getSymbolicVariables()
            other_vars = other.stmt.getSymbolicVariables()
            if len(my_vars) != len(other_vars):
                return False
            for i in range(0, len(my_vars)):
                if isinstance(my_vars[i], SymbolicExpression):
                    if not my_vars[i].symbolicEq(other_vars[i]):
                        return False
                elif my_vars[i] is not other_vars[i]:
                    return False
            return True
        else:
            return False

    def __hash__(self):
        return hash(self.stmt.opcode_id)

    def negate(self):
        """Negates the current predicate"""
        assert(self.result is not None)
        self.result = not self.result

    def needsSTP(self):
        if isinstance(self.stmt.condition, bc.FunctionCall) and self.stmt.condition.name[-7:] == "has_key":
            return False
        else:
            return True

    def buildSTP(self, context):
        if self.stmt == None:
            utils.crash("Predicate without statement")
        self.stmt.refreshRef(context)
        if self.result == None:
            utils.crash("This predicate has an unknown result: %s" % self)

        stp = stp_mod._stp

        if self.needsSTP():
            c = self.stmt.condition
            bitlen = c.getBitLength()
            stp_expr = self.buildSTPExprFromStatement(stp, c, bitlen)
            if not stp_expr.getType().isBool():
                # make it boolean, stp does not like things like (a & 1) used as boolean expressions
                # so we transform it in (a & 1) != 0, but STP does not have !=, so we use !((a & 1) == 0)
                stp_expr = stp.notExpr(stp.eqExpr(stp_expr, stp_mod.int2stp(0, bitlen)))
            if not self.result:
                stp_expr = stp.notExpr(stp_expr)

            return (True, stp_expr)
        log.error("Cannot fix predicate %s, skipping" % self)
        return (False, None)

    def __str__(self):
        return str(self.stmt) + " (was %s)" % (self.result)

    def __repr__(self):
        return repr(self.stmt) + " (was %s)" % (self.result)

    def buildSTPExprFromStatement(self, stp, stmt, bitlen):
        """This function is recursive"""
        if isinstance(stmt, bc.BinaryOperator):
            STPLeft = self.buildSTPExprFromStatement(stp, stmt.left, bitlen)
            STPRight = self.buildSTPExprFromStatement(stp, stmt.right, bitlen)
            if stmt.name == "==":
                return stp.eqExpr(STPLeft, STPRight)
            if stmt.name == "&":
                return stp.bvAndExpr(STPLeft, STPRight)
            if stmt.name == "<":
                return stp.sbvLtExpr(STPLeft, STPRight)
            if stmt.name == ">":
                return stp.sbvGtExpr(STPLeft, STPRight)
            if stmt.name == "<=":
                return stp.sbvLeExpr(STPLeft, STPRight)
            if stmt.name == ">=":
                return stp.sbvGeExpr(STPLeft, STPRight)
            if stmt.name == "!=":
                return stp.notExpr(stp.eqExpr(STPLeft, STPRight))
            else:
                utils.crash("Cannot build STP for unknown operator %s" % stmt.name)
        elif isinstance(stmt, bc.Attribute) or isinstance(stmt, bc.LocalReference) or isinstance(stmt, bc.GlobalReference) or isinstance(stmt, bc.Subscr):
            if stmt.isSymbolic():
                sym_var = stmt.reference # could be an expression
                stpvars = sym_var.getSTPVariable()
                for name, var, stp_var in stpvars:
                    self.stp_variables[name] = (var, stp_var)
                if isinstance(sym_var, SymbolicExpression):
                    return stp_mod.ast2stp(sym_var.expr, sym_var.getBitLength())
                else:
                    return stpvars[0][2]
            else:
                v = long(stmt.value) # Try to get an int
                return stp_mod.int2stp(v, bitlen)
        elif isinstance(stmt, bc.FunctionCall):
            if stmt.name == "ord": # We know that our ord does nothing
                return self.buildSTPExprFromStatement(stp, stmt.params[0], bitlen)
            elif stmt.name[-7:] == "has_key":
                utils.crash("Cannot build STP for has_key call %s" % stmt.name)
            else:
                utils.crash("Cannot build STP for unknown function %s" % stmt.name)
        elif isinstance(stmt, bc.ConstantValue):
            v = long(stmt.reference)
            return stp_mod.int2stp(v, bitlen)
        elif isinstance(stmt, bc.UnaryOperator):
            if stmt.name == "not":
                e = self.buildSTPExprFromStatement(stp, stmt.expr, bitlen)
                if e.getType().isBool():
                    return stp_mod.notExpr(e)
                else:
                    # make it boolean, stp does not like things like (a & 1) used as boolean expressions
                    # so we transform the whole not expression to (a & 1) == 0
                    return stp_mod.eqExpr(e, stp_mod.int2stp(0, bitlen))
            else:
                utils.crash("Unkown unary operator %s" % stmt.name)
        else:
            utils.crash("Cannot build STP for unknown class %s" % stmt.__class__.__name__)

