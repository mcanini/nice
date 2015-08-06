from translator_utils import createScapyPacket

from scapy_mod import *

from oftest.cstruct import *
from oftest.message import *
from oftest.action import * 
from oftest.action_list import *

def compareResults(switch, packets, queries, expectedPackets, expectedQueries):
    val = True
    errors = {}
    for key in switch.portMap.keys():
        val2, errors[key.type] = compareResultsDetails(switch.portMap[key], packets[key.type], queries[key.type], expectedPackets, expectedQueries)
        val = val and val2
        
    return val, errors

def compareResultsDetails(portMap, packets, queries, expectedPackets, expectedQueries):
    packets.sort()
    expectedPackets = map(lambda (node, port, packet): (node.ports_object[port].peer_port, createScapyPacket(packet)), expectedPackets)
    expectedPackets.sort()

    errors = []

    if len(packets) != len(expectedPackets) or len(queries) != len(expectedQueries):
        errors.append(("wrong counts", (len(packets), len(expectedPackets), len(queries), len(expectedQueries)) ))
        return False, errors

    for i in range(len(expectedPackets)):
        if Padding in packets[i][1]:
            zero_index = packets[i][1][Padding].load.find("\x00")
            if zero_index >= 0:
                packets[i][1][Padding].load = packets[i][1][Padding].load[:zero_index]
        if Raw in packets[i][1]:
            zero_index = packets[i][1][Raw].load.find("\x00")
            if zero_index >= 0:
                packets[i][1][Raw].load = packets[i][1][Raw].load[:zero_index]
        if packets[i] != expectedPackets[i]:
            errors.append(("wrong packets", (packets[i], expectedPackets[i]) ))
            return False, errors

    for i in range(len(expectedQueries)):
        (buffer_id, packet, inport, reason, max_length) = expectedQueries[i]
        packet = createScapyPacket(packet)

        realQuery = queries[i]

        if realQuery.header.type != 10 or realQuery.reason != reason or realQuery.in_port != portMap[inport]:
            errors.append(("query header", (realQuery.header.type, realQuery.in_port, inport, realQuery.reason, reason) ))
            return False, errors

        s1 = str(realQuery.data)        #TODO: error if someone sends too much
#       if len(s1) > max_length:
#           s1 = s1[:max_length]
        k = len(s1)
        while k > 0 and s1[k - 1] == '\x00':
            k -= 1
            s1 = s1[:-1]
        s2 = str(packet)
        if len(s2) > max_length:
            s2 = s2[:max_length]
        k = len(s2)
        while k > 0 and s2[k - 1] == '\x00':
            k -= 1
            s2 = s2[:-1]
        
        if s1 != s2:
            errors.append(("query data", (s1, s2) ))
            return False, errors

    return True, errors

def comparePortStats(switch, stats):
    checked = []
    errors = []
    for key1 in switch.portMap.keys():
        stat1 = stats[key1.type]
        for st1 in stat1.stats:
            p = filter(lambda x: switch.portMap[key1][x] == st1.port_no, switch.portMap[key1])
            if len(p) > 0:
                st1.port_no = p[0]
                st1.pad= [0,0,0,0,0,0]

    for key1 in stats:
        checked.append(key1)
        for key2 in stats:
            if key2 in checked:
                continue

            stat1 = stats[key1]
            stat2 = stats[key2]

            if len(stat1.stats) != len(stat2.stats):
                errors.append(("port stats wrong count", (key1, key2, stat1.stats, stat2.stats)) )
                continue

            for st1 in stat1.stats:
                found = False
                for st2 in stat2.stats:
                    if found:
                        break
                    if st1.port_no == st2.port_no:
                        found = True
                        if st1.rx_packets != st2.rx_packets or st1.tx_packets != st2.tx_packets:# or st1.rx_bytes != st2.rx_bytes or st1.tx_bytes != st2.tx_bytes:
                            errors.append(("flow stats not match", (key1, key2, st1.show(), st2.show())) )
                if not found:
                    errors.append(("no matching port for stats", (key1, key2, st1.port_no)) )

    return len(errors) == 0, errors

def compareFlowStats(switch, stats):
    checked = []
    errors = []
    for key1 in switch.portMap.keys():
        stat1 = stats[key1.type]
        for st1 in stat1.stats:
            if st1.match.wildcards & 1 == 1:
                st1.match.in_port = 0
            else:
                p = filter(lambda x: switch.portMap[key1][x] == st1.match.in_port, switch.portMap[key1])
                if len(p) > 0:
                    st1.match.in_port = p[0]
            st1.match.pad1 = 0
            st1.match.pad2 = [0,0]

    for key1 in stats:
        checked.append(key1)
        for key2 in stats:
            if key2 in checked:
                continue

            stat1 = stats[key1]
            stat2 = stats[key2]
            print "LL", len(stat1.stats), len(stat2.stats)
            if len(stat1.stats) != len(stat2.stats):
                errors.append(("flow stats wrong count", (key1, key2, stat1.stats, stat2.stats)) )
                continue

            for st1 in stat1.stats:
                found = False
                for st2 in stat2.stats:
                    if found:
                        break
                    print st2.match.show()
                    if st1.match == st2.match:
                        found = True
                        if st1.packet_count != st2.packet_count or st1.byte_count != st2.byte_count:
                            errors.append(("flow stats not match", (key1, key2, st1.match.show(), st1.packet_count, st2.packet_count, st1.byte_count, st2.byte_count)) )
                if not found:
                    errors.append(("no matching flow for stats", (key1, key2, st1.match.show())) )

    return len(errors) == 0, errors

