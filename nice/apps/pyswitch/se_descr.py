import struct
from symbolic import invocation
# Do not import you packages here, but do it in the callbacks below.
# Otherwise the application will run with non-instrumented versions of those modules.

class SymExecDescr:
    APP_NAME="pyswitch NOX app"
    NORMALIZE_MODS = ["pyswitch.py", "custom_constraints.py"] # list of single modules (filenames with relative path from current dir) to normalize
    NORMALIZE_PACKAGES = [] # As above, but for packages. The normalization will be recursive and cover the full package
    USES_NOX_API = True # This will cause the NOX SE library to be instrumented and copied in the import PATH

    def __init__(self, _num_invocations):
        self.nox_app_name = "pyswitch"
        self.pyswitch = None
        self.invocation = None
        self.mac_addresses = []

    def create_invocations(self, macs=[]):
        from nox.lib.packet import ethernet
        inv = invocation.NicePacketInInvocation(self.run)
        inv.addParameter("dpid", 0)
        inv.addParameter("inport", 0)
        inv.addParameter("reason", 0)
        inv.addParameter("len", 0)
        inv.addParameter("bufid", 0)
        inv.addSymbolicParameter("packet", "packet0", ethernet.ethernet)
        self.invocation = inv
        self.mac_addresses = macs
        return [inv]

    def reset_callback(self):
        self.app = __import__(self.nox_app_name)
        assert self.invocation != None
        app_obj = getattr(self.app, self.nox_app_name)(None) # Pass an empty context
        app_obj.install() # initialize the app

        # See the __getstate__ function added to pyswitch app
        if self.invocation.state != None:
            for dpid in self.invocation.state["st"]:
                app_obj.st["dpid"] = {}
                for m_u in self.invocation.state["st"][dpid]:
                    m = struct.pack("BBBBBB", *m_u)
                    app_obj.st["dpid"][m] = (self.invocation.state["st"][dpid][m_u], 0, None)

#       print "Resetting app with state: %s" % app_obj.st

    def run(self, **args):
        custom_constraints = __import__("custom_constraints")
        custom_constraints.run(self.app, self.mac_addresses, **args)

    def execution_complete(self, return_values):
        return
#       for i in range(0, len(return_vals)):
#           print "Iter %d returned %s" % (i, map(ret2str, return_vals[i]))

    def ret2str(self, ret):
        if ret == 0:
            return "CONTINUE"
        elif ret == 1:
            return "STOP"
        else:
            return "unknown return value"

def factory(param):
    if len(param) == 0:
        return SymExecDescr(1)
    else:
        return SymExecDescr(int(param[0]))

