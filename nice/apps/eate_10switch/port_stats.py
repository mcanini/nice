from symbolic.symbolic_types.integers import SymbolicInteger
from symbolic.symbolic_types.symbolic_type import SymbolicType

class port_stats_data(SymbolicType):
    def __init__(self, symbolic_name):
        SymbolicType.__init__(self, symbolic_name)
        p1 = {"port_no" : 1,
            "tx_packets" : SymbolicInteger(symbolic_name + "#p1txp", 32),
            "tx_bytes" : SymbolicInteger(symbolic_name + "#p1txb", 32),
            }
        p2 = {"port_no" : 2,
            "tx_packets" : SymbolicInteger(symbolic_name + "#p2txp", 32),
            "tx_bytes" : SymbolicInteger(symbolic_name + "#p2txb", 32),
            }
        p3 = {"port_no" : 3,
            "tx_packets" : SymbolicInteger(symbolic_name + "#p3txp", 32),
            "tx_bytes" : SymbolicInteger(symbolic_name + "#p3txb", 32),
            }
        self.data = [p1, p2, p3]

    def getConcrValue(self):
        return [
            {"port_no" : 1,
             "tx_packets" : self.data[0]["tx_packets"].getConcrValue(),
             "tx_bytes" : self.data[0]["tx_bytes"].getConcrValue(),
             },
            {"port_no" : 2,
             "tx_packets" : self.data[1]["tx_packets"].getConcrValue(),
             "tx_bytes" : self.data[1]["tx_bytes"].getConcrValue(),
             },
            {"port_no" : 3,
             "tx_packets" : self.data[2]["tx_packets"].getConcrValue(),
             "tx_bytes" : self.data[2]["tx_bytes"].getConcrValue(),
             },
            ]

    def __iter__(self):
        return iter(self.data)
