from symbolic import invocation
from symbolic.symbolic_types.symbolic_store import newInteger

class ManyBranchesTest(object):
    _EXPECTED_RETVALUES = [1, 2, 3, 4, 5, 6, 7, 8]
    _NAME = "many_branches"
    
    def reload(self):
        self.app = __import__("many_branches")

    def _runner(self, **args):
        return self.app.many_branches(**args)

    def create_invocations(self):
        inv = invocation.FunctionInvocation(self._runner)
        inv.addSymbolicParameter("in1", "in1", newInteger)
        inv.addSymbolicParameter("in2", "in2", newInteger)
        inv.addSymbolicParameter("in3", "in3", newInteger)
        return [inv]

Test = ManyBranchesTest
