from symbolic import invocation
from symbolic.symbolic_types.symbolic_store import newInteger

class AssignTest(object):
    _EXPECTED_RETVALUES = [0, 1, 2]
    _NAME = "assign"
    
    def reload(self):
        self.app = __import__("assign")

    def _runner(self, **args):
        return self.app.assign(**args)

    def create_invocations(self):
        inv = invocation.FunctionInvocation(self._runner)
        inv.addSymbolicParameter("in1", "in1", newInteger)
        inv.addSymbolicParameter("in2", "in2", newInteger)
        return [inv]

Test = AssignTest
