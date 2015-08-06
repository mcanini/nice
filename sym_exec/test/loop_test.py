from symbolic import invocation
from symbolic.symbolic_types.symbolic_store import newInteger

class LoopTest(object):
    _EXPECTED_RETVALUES = [0, 2, 2]
    _NAME = "loop"
    
    def reload(self):
        self.app = __import__("loop")

    def _runner(self, **args):
        return self.app.loop(**args)

    def create_invocations(self):
        inv = invocation.FunctionInvocation(self._runner)
        inv.addSymbolicParameter("in1", "in1", newInteger)
        inv.addSymbolicParameter("in2", "in2", newInteger)
        return [inv]

Test = LoopTest

