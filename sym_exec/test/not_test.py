from symbolic import invocation
from symbolic.symbolic_types.symbolic_store import newInteger

class NotTest(object):
    _EXPECTED_RETVALUES = [0, 1, 2, 3, 4]
    _NAME = "not"
    
    def reload(self):
        self.app = __import__("not")

    def _runner(self, **args):
        return self.app.not_inside_if(**args)

    def create_invocations(self):
        inv = invocation.FunctionInvocation(self._runner)
        inv.addSymbolicParameter("in1", "in1", newInteger)
        inv.addSymbolicParameter("in2", "in2", newInteger)
        inv.addSymbolicParameter("in3", "in3", newInteger)
        return [inv]

Test = NotTest
