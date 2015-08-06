from scapy.all import *

def mysniff(ifaces = [], prn = None, timeout=None, shouldStop=None, lo_listening = None, *arg, **karg):
    sockets = []
    lst = []

    for iface in ifaces:
#       if L2socket is None:
#           L2socket = conf.L2listen
        L2socket = MyL2ListenSocket
        sockets.append(L2socket(type=ETH_P_ALL, iface=iface[0], filter=iface[1], *arg, **karg))

    while 1:
        if shouldStop is not None and shouldStop():
            break

        if lo_listening is not None:
            lo_listening.set()

        sel = select(sockets,[],[],timeout)

        for s in sel[0]:
            p, sa_ll = s.recv(MTU)
            if p is None:
                continue
            lst.append(p)
            if prn:
                prn(p, sa_ll)

    for s in sockets:
        s.close()

    return plist.PacketList(lst,"Sniffed")

class MyL2ListenSocket(L2ListenSocket):
    def recv(self, x):
        pkt, sa_ll = self.ins.recvfrom(x)
        if sa_ll[2] == socket.PACKET_OUTGOING:
            return (None, sa_ll)

        if sa_ll[3] in conf.l2types :
            cls = conf.l2types[sa_ll[3]]
        elif sa_ll[1] in conf.l3types:
            cls = conf.l3types[sa_ll[1]]
        else:
            cls = conf.default_l2
            warning("Unable to guess type (interface=%s protocol=%#x family=%i). Using %s" % (sa_ll[0],sa_ll[1],sa_ll[3],cls.name))

        try:
            pkt = cls(pkt)
        except KeyboardInterrupt:
            raise
        except:
            if conf.debug_dissector:
                raise
            pkt = conf.raw_layer(pkt)
        pkt.time = get_last_packet_timestamp(self.ins)
        return (pkt, sa_ll)

