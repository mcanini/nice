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

import logging
from ConfigParser import SafeConfigParser
from StringIO import StringIO

_default_config = StringIO("""
[model]
name = LoadBalancerModel
app_dir = loadbalancer
app_descr = none
cutoff = -1
faults = 0
flow_entry_expiration = false
use_real_switch = False
switch_failures = False

[nice_model]
max_pkts = 2
max_burst = 1

[pyswitch_model]
pkts = 2
sequential = False
move_host = False

[eate_model]
connections = 1
app_version = eateb

[loadbalancer_model]
connections = 2
use_fixed_version = None

[twohosts_model]
pkts = 2

[strategy]
dpor = False
name = CompleteCoverage

[randomwalk]
seed = -1

[runtime]
log_level = info
""")

_values = {}

def init(fname):
    parser = SafeConfigParser()
    parser.readfp(_default_config)
    parser.readfp(open(fname))

    for s in parser.sections():
        for o in parser.options(s):
            _values[s + "." + o] = parser.get(s, o)

    convertTypes()

def convertTypes():
    for k in _values:
        if k == "runtime.log_level":
            _values[k] = getLogLevel(k)
        elif tryToInt(k):
            continue
        elif tryToBool(k):
            continue
        elif tryToNone(k):
            continue

def tryToInt(k):
    try:
        _values[k] = int(_values[k])
    except (ValueError, TypeError):
        return False
    else:
        return True

def tryToBool(k):
    if _values[k] == "true" or _values[k] == "True":
        _values[k] = True
    elif _values[k] == "false" or _values[k] == "False":
        _values[k] = False
    else:
        return False
    return True

def tryToNone(k):
    if _values[k] == "none" or _values[k] == "None":
        _values[k] = None
    else:
        return False
    return True

def get(key):
    return _values[key]

def set(key, value):
    _values[key] = value

def getLogLevel(k):
    name = get(k)
    if name in [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]:
        return name
    elif name == "debug":
        return logging.DEBUG
    elif name == "info":
        return logging.INFO
    elif name == "warning":
        return logging.WARNING
    elif name == "error":
        return logging.ERROR
    elif name == "critical":
        return logging.CRITICAL
    else:
        return None

