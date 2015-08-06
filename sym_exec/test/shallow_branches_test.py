from symbolic import invocation
from symbolic.symbolic_types.symbolic_store import newInteger

class ShallowBranchesTest(object):
    _EXPECTED_RETVALUES = [0, 1, 3, 5, 7, 9]
    _NAME = "shallow_branches"
    
    def reload(self):
        self.app = __import__("shallow_branches")

    def _runner(self, **args):
        return self.app.shallow_branches(**args)

    def create_invocations(self):
        inv = invocation.FunctionInvocation(self._runner)
        inv.addSymbolicParameter("in1", "in1", newInteger)
        inv.addSymbolicParameter("in2", "in2", newInteger)
        inv.addSymbolicParameter("in3", "in3", newInteger)
        inv.addSymbolicParameter("in4", "in4", newInteger)
        inv.addSymbolicParameter("in5", "in5", newInteger)
        return [inv]

Test = ShallowBranchesTest
