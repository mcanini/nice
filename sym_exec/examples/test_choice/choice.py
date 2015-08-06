# vim: set expandtab ts=4 sw=4:
# Test if engine explores all paths

import symbolic.types.symbolic_store as symbolic_store

inst = None

def make_choice(n):
    """ return one of n symbolic choices 0..n-1"""
    c = symbolic_store.newInteger("choice", 32);
    for x in range(0, n-1):
        if c == x:
            return x
    return n - 1

def test():
    print "making choice:"
    c = make_choice(10)
    print "choice is ", c

    return

class choice():

    def __init__(self, ctxt):
        pass

    def install(self):
        pass

    def getInterface(self):
        return str(dictionary)
