from symbolic import invocation
from symbolic.symbolic_types.symbolic_store import newInteger
from nox.lib.packet.ethernet import ethernet

class CountPacketsTest(object):
    _EXPECTED_RETVALUES = [
        {'lldp': 1, 'normal': 1},
        {'lldp': 1, 'normal': 1},
    ]
    _NAME = "count_packets"
    
    def reload(self):
        self.app = __import__("count_packets")

    def _runner(self, **args):
        return self.app.packet_in_callback(**args)

    def create_invocations(self):
        inv = invocation.FunctionInvocation(self._runner)
        inv.addParameter("cnt", {'lldp' : 0, 'normal' : 0})
        inv.addSymbolicParameter("packet", "packet", ethernet)
        return [inv]

Test = CountPacketsTest



