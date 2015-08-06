from symbolic import invocation
from symbolic.symbolic_types.symbolic_store import newInteger

class ElifTest(object):
    _EXPECTED_RETVALUES = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    _NAME = "elseif"
    
    def reload(self):
        self.app = __import__("elseif")

    def _runner(self, **args):
        return self.app.elseif(**args)

    def create_invocations(self):
        inv = invocation.FunctionInvocation(self._runner)
        inv.addSymbolicParameter("in1", "in1", newInteger)
        return [inv]

Test = ElifTest

