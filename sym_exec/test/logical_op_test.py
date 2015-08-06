from symbolic import invocation
from symbolic.symbolic_types.symbolic_store import newInteger

class LogicalOpTest(object):
    _EXPECTED_RETVALUES = [2, 3]
    _NAME = "logical_op"
    
    def reload(self):
        self.app = __import__("logical_op")

    def _runner(self, **args):
        return self.app.logical_op(**args)

    def create_invocations(self):
        inv = invocation.FunctionInvocation(self._runner)
        inv.addSymbolicParameter("in1", "in1", newInteger)
        inv.addSymbolicParameter("in2", "in2", newInteger)
        return [inv]

Test = LogicalOpTest

