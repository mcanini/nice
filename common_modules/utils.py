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

import sys
import traceback
import logging
log = logging.getLogger("nice.utils")

def _traceback():
    stack = traceback.format_stack()
    return stack[:-2]

def crash(msg):
    stack = _traceback()
    log.critical("\n"+"".join(stack))
    log.critical(msg)
    sys.exit(-1)

def printStackTrace():
    log.debug("".join(_traceback()))

def _check_iterable(obj):
        try:
            iter(obj)
        except TypeError:
            return False
        else:
            return True

id_counters = {}
def getID(key):
    if key in id_counters:
        id_counters[key] += 1
    else:
        id_counters[key] = 0
    return id_counters[key]

BASE_TYPES = [int, str, type(None), bool, long]
def copy_state(obj):
    if hasattr(obj, "dump_equivalent_state"):
        return obj.dump_equivalent_state()
    elif isinstance(obj, dict):
        return serialize_dict(obj)
    elif type(obj) in BASE_TYPES:
        return obj
    elif isinstance(obj, tuple):
        return tuple([ copy_state(x) for x in obj ]) # do not reorder tuples
    elif _check_iterable(obj):
        return [ copy_state(x) for x in sorted(obj) ]
    else:
        crash("Type of " + str(obj) + " is " + str(type(obj)) + " " + obj.__class__.__name__)

def serialize_dict(d):
    nd = {}
    keys = d.keys()
    keys.sort()
    for k in keys:
        nd[k] = copy_state(d[k])
#       if isinstance(d[k], dict):
#           nd[k] = serialize_dict(d[k])
#       elif hasattr(d[k], "dump_equivalent_state"):
#           nd[k] = d[k].dump_equivalent_state()
#       elif hasattr(d[k], "__getstate__"):
#           nd[k] = d[k].__getstate__()
#       else:
#           crash("")
#           nd[k] = d[k]
    return nd

def flatten_dict(d):
    keys = d.keys()
    keys.sort()
    flat_attrs = map(lambda x: (x, d[x]), keys)
    return [item for subtuple in flat_attrs for item in subtuple] # Flatten the list of tuples

def serialize_list_of_dicts(l):
    nl = []
    for d in l:
        nd = serialize_dict(d)
        nl.append(nd)
    nl.sort(key=flatten_dict)
    return nl

