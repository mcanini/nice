import copy
from symbolic import invocation
from port_stats import port_stats_data
# Do not import you packages here, but do it in the callbacks below.
# Otherwise the application will run with non-instrumented versions of those modules.

class SymExecApp:
    APP_NAME="eate 10 switch NOX app"
    NORMALIZE_MODS = ["eate_10switch.py"] # list of single modules (filenames with relative path from current dir) to normalize
    NORMALIZE_PACKAGES = [] # As above, but for packages. The normalization will be recursive and cover the full package
    USES_NOX_API = True # This will cause the NOX SE library to be instrumented and copied in the import PATH

    def __init__(self, _num_invocations):
        self.nox_app_name = "eate_10switch"
        self.pyswitch = None
        self.invocation = None
        self.mac_addresses = []

    def create_invocations(self, macs=[]):
        from nox.lib.packet import ethernet
        inv = invocation.NicePortStatsInInvocation(self.run)
        inv.addParameter("dpid", 1)
        inv.addSymbolicParameter("ports", "stats0", port_stats_data)
        self.invocation = inv
        #self.mac_addresses = macs
        return [inv]

    def reset_callback(self):
        self.app = __import__(self.nox_app_name, fromlist="eate_app")
        assert self.invocation != None
        app_obj = getattr(self.app, "eate")(None) # Pass an empty context
        app_obj.install() # initialize the app

        if self.invocation.state != None:
            #TODO(ppershing): why following line does not work?
            #app_obj.__setstate__(self.invocation.state)
            app_obj.dp_port_stats = copy.copy(self.invocation.state["dp_port_stats"])

#       print "Resetting app with state: %s" % app_obj.st

    def run(self, **args):
        self.app.inst.port_stats_in_handler(**args)

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
        return SymExecApp(1)
    else:
        return SymExecApp(int(param[0]))

