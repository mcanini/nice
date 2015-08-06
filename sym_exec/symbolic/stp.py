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

import ast

import logging
log = logging.getLogger("nice.se.stp")
import utils

try:
    import pystp
except ImportError as e:
    utils.crash("Cannot import %s" % e)

from symbolic.symbolic_types.symbolic_type import SymbolicType

_stp = pystp.Stp()

stp_types = {}
stp_vars = {}

def int2stp(v, length):
    # see note on getIntegerType
    return _stp.bvConstExprFromLL(length, v)

def getIntegerType(bitlen):
    ### Note: Pystp threats int as 32 bit and using getBVInt / getBVUnsigned
    # with 64bit architecture can cause following crash when stp counterexample contains >32bit values:
    #    Fatal Error: GetUnsignedConst: cannot convert bvconst of length greater than 32 to unsigned int
    #    python: ASTmisc.cpp:92: void BEEV::FatalError(const char*): Assertion `0' failed.
    #    Aborted
    # TODO: fix pystp C implementation, it is using deprecated function GetUnsignedConst from stp/AST/AST.h:
    if not stp_types.has_key(bitlen):
        stp_types[bitlen] = _stp.createType(pystp.TYPE_BITVECTOR, bitlen)
    return stp_types[bitlen]

def newIntegerVariable(name, bitlen):
    if name not in stp_vars:
        stp_vars[name] = _stp.varExpr(name, getIntegerType(bitlen))
    else:
        log.error("Trying to create a duplicate variable")
    return stp_vars[name]

def newMacVariable(name):
    if name not in stp_vars:
        stp_vars[name] = _stp.varExpr(name, getIntegerType(48))
    else:
        log.error("Trying to create a duplicate variable")
    return stp_vars[name]

def findCounterexample(stp_asserts, stp_query, stp_variables):
    """Tries to find a counterexample to the query while
       asserts remains valid."""
    _stp.push()
    for e in stp_asserts:
        _stp.assertFormula(e)
    ret = _stp.query(stp_query)
    if ret == 1:
        log.warning("STP rejected the query, impossible to solve?")
#       log.debug("Variables were:")
#       _stp.printVarDecls()
#       log.debug("Query was:")
#       log.debug(stp_query)
#       log.debug("Assertions defined:")
#       _stp.printAsserts()
        _stp.pop()
        return None
    elif ret == 2:
        log.error("STP reported an error")
        _stp.pop()
        return None

#   _stp.printAsserts()
#   _stp.printVarDecls()

    res = []
    for var_name in stp_variables:
        (instance, stp_var) = stp_variables[var_name]
        ce = _stp.getCounterExample(stp_var)
        res.append((var_name, instance, ce.getBVUnsignedLongLong()))
#       print var, instance
#       var = var.getUnderivedParent()
#       print var.getSTP(self.stp)
#       _stp.printCounterExample()
#       ce = self.stp.getCounterExample(var.getSTP(self.stp))
#       self.input_variables[var.name] = ce.getBVUnsigned() # NOTE variables can be only integers

    _stp.pop()
    return res

def notExpr(expr):
    return _stp.notExpr(expr)

def extract(var, start, end):
    return _stp.bvExtract(var, start, end)

def eqExpr(e1, e2):
    return _stp.eqExpr(e1, e1)

def ast2stp(expr, bitlen):
    if isinstance(expr, ast.BinOp):
        stp_l = ast2stp(expr.left, bitlen)
        stp_r = ast2stp(expr.right, bitlen)
        if isinstance(expr.op, ast.Add):
            return _stp.bvPlusExpr(bitlen, stp_l, stp_r)
        elif isinstance(expr.op, ast.Sub):
            return _stp.bvMinusExpr(bitlen, stp_l, stp_r)
        elif isinstance(expr.op, ast.Mult):
            return _stp.bvMultExpr(bitlen, stp_l, stp_r)
        elif isinstance(expr.op, ast.Eq):
            return _stp.eqExpr(stp_l, stp_r)
        else:
            utils.crash("Unknown BinOp during conversion from ast to stp (expressions): %s" % expr.op)
    elif isinstance(expr, SymbolicType):
        return expr.getSTPVariable()[0][2]
    elif isinstance(expr, int) or isinstance(expr, long):
        return int2stp(expr, bitlen)
    else:
        utils.crash("Unknown node during conversion from ast to stp (expressions): %s" % expr)

def resetVarCache():
    # deleting the variables makes stp crash, doing pop and push does not work, this is the
    # only way to have a clean STP environment """
    global _stp
    del _stp
    _stp = pystp.Stp()
    stp_vars.clear()

