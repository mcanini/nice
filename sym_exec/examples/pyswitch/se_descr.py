from symbolic import invocation
# Do not import you packages here, but do it in the callbacks below.
# Otherwise the application will run with non-instrumented versions of those modules.

class SymExecApp:
    APP_NAME="pyswitch NOX app"
    NORMALIZE_MODS = ["pyswitch.py"] # list of single modules (filenames with relative path from current dir) to normalize
    NORMALIZE_PACKAGES = [] # As above, but for packages. The normalization will be recursive and cover the full package
    USES_NOX_API = True # This will cause the NOX SE library to be instrumented and copied in the import PATH

    def __init__(self, num_invocations):
        self.nox_app_name = "pyswitch"
        self.invocation_count = num_invocations
        self.pyswitch = None

    def create_invocations(self):
        from nox.lib.packet import ethernet
        invocation_sequence = []
        for i in range(self.invocation_count):
            inv = invocation.FunctionInvocation(self.run)
            inv.addParameter("dpid", 0)
            inv.addParameter("inport", 0)
            inv.addParameter("reason", 0)
            inv.addParameter("len", 0)
            inv.addParameter("bufid", 0)
            inv.addSymbolicParameter("packet", "packet%d" % i, ethernet.ethernet)
            invocation_sequence.append(inv)
        return invocation_sequence

    def reset_callback(self):
        self.app = __import__(self.nox_app_name)
        app_obj = getattr(self.app, self.nox_app_name)(None) # Pass an empty context
        app_obj.install() # initialize the app, in pyswitch this does nothing useful

    def run(self, **args):
        self.app.packet_in_callback(**args)

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

