from symbolic import invocation
from symbolic.symbolic_types.symbolic_store import newInteger

class DictionaryTest(object):
    _EXPECTED_RETVALUES = [1, 2]
    _NAME = "dictionary"
    
    def reload(self):
        self.app = __import__("dictionary")

    def _runner(self, **args):
        return self.app.dictionary(**args)

    def create_invocations(self):
        inv = invocation.FunctionInvocation(self._runner)
        inv.addSymbolicParameter("in1", "in1", newInteger)
        return [inv]

Test = DictionaryTest
