debug_mac_addresses = [0x001122334455, 0x00aa55aa55aa]
debug_mac_addresses = [0x00BAADF00D01, 0x000102030405]

def run(app, mac_addresses, **args):
    #if mac_addresses == []:
    #   mac_addresses = debug_mac_addresses
#   stop = len(mac_addresses)
#   cur = 0
    pkt = args["packet"]
    if pkt.src == mac_addresses[0] and pkt.dst == mac_addresses[1]:
        pass
#   if pkt.src == mac_addresses[1] and pkt.dst == mac_addresses[0]:
#       pass

#   while cur < stop:
#       mac = mac_addresses[cur]
#       if pkt.src == mac and pkt.src != pkt.dst:
#           pass
#       if pkt.dst == mac and pkt.src != pkt.dst:
#           pass
#       cur = cur + 1
    app.packet_in_callback(**args)

