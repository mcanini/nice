#
# Copyright (c) 2011, EPFL (Ecole Politechnique Federale de Lausanne)
# All rights reserved.
#
# Created by Marco Canini, Daniele Venzano, Dejan Kostic, Jennifer Rexford
# To this file contributed: Peter Peresini
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

from symbolic import invocation
from symbolic.symbolic_types.symbolic_store import newInteger
# Do not import you packages here, but do it in the callbacks below.
# Otherwise the application will run with non-instrumented versions of those modules.


class SymExecApp:
    APP_NAME="SE regression test suite"
    # list of single modules (filenames with relative path from current dir) to normalize
    NORMALIZE_MODS = [
        "many_branches.py",
        "shallow_branches.py",
        "loop.py",
        "logical_op.py",
        "elseif.py",
        "dictionary.py",
        "count_packets.py",
        "expressions.py",
        "not.py",
        "assign.py",
    ] 
    NORMALIZE_PACKAGES = [] # As above, but for packages. The normalization will be recursive and cover the full package
    USES_NOX_API = True # This will cause the NOX SE library to be instrumented and copied in the import PATH
    def __init__(self, which_test):
        import imp
        import os.path
        module_name = "%s_test" % which_test
        module_path = "%s/%s.py" % (os.path.dirname(__file__), module_name)
        module = imp.load_source(module_name, module_path)
        self.test = module.Test()

    def create_invocations(self):
        return self.test.create_invocations()

    def reset_callback(self):
        return self.test.reload()

    def check(self, computed, expected):
        if len(computed) != len(expected) or computed != expected:
            print "-------------------> %s test failed <---------------------" % self.test._NAME
            print "Expected: %s, found: %s" % (expected, computed)
        else:
            print "%s test passed <---" % self.test._NAME

    def execution_complete(self, return_vals):
        res = sorted([x[0] for x in return_vals])
        expected = sorted(self.test._EXPECTED_RETVALUES)
        self.check(res, expected)
    
def factory(param):
    return SymExecApp(param[0])

