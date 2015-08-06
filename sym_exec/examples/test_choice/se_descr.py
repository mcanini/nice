from symbolic import invocation
# Do not import you packages here, but do it in the callbacks below.
# Otherwise the application will run with non-instrumented versions of those modules.

class SymExecApp:
    APP_NAME="pyswitch NOX app"
    NORMALIZE_MODS = ["choice.py"] # list of single modules (filenames with relative path from current dir) to normalize
    NORMALIZE_PACKAGES = []

    def __init__(self):
        self.nox_app_name = "choice"
        self.pyswitch = None

    def create_invocations(self):
        inv = invocation.FunctionInvocation(self.run)
        return [inv]

    def reset_callback(self):
        self.app = __import__(self.nox_app_name)
        app_obj = getattr(self.app, self.nox_app_name)(None) # Pass an empty context
        app_obj.install() # initialize the app, in pyswitch this does nothing useful

    def run(self, **args):
        self.app.test(**args)

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

def factory():
    return SymExecApp()

