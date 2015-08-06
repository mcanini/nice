import os, select, time
from subprocess import Popen, PIPE, STDOUT

class VirtualSwitch:
    def __init__(self, switch, controller_ip, controller_port):
        self.switch = switch
        self.openflow_id = switch.openflow_id + self.__class__.value
        self.ports = []
        for port in self.switch.ports_object:
            if self.switch.ports_object[port] is not None and self.switch.ports_object[port].peer is not None:
                self.ports.append(self.switch.ports_object[port].name)
        self.controller_ip = controller_ip
        self.controller_port = controller_port
        self.type = ""


    def runCmd(self, cmd):
        popen = Popen(cmd.split( ' ' ), stdout=PIPE, stderr=STDOUT, close_fds = True )
        output = ''
        readable = select.poll()
        readable.register( popen.stdout )
        while True:
            while readable.poll():
                data = popen.stdout.read( 1024 )
                if len( data ) == 0:
                    break
                output += data
            popen.poll()
            if popen.returncode != None:
                break
        popen.stdout.close()
        del popen
        return output

    def runSwitchCmd(self, cmd):
        os.write( self.shell.stdin.fileno(), cmd + ' printf "\\177" \n')
#       a = 0
#       while True:
#           if a == 0:
#               self.pollOut.poll()     
#           data = os.read( self.shell.stdout.fileno(), 1024 )
#           if chr( 127 ) in data:
#               break;


    def createVirtualInterfaces(self):
        if len(self.switch.realIfaces[self.__class__]) > 0:
            return

        self.removeVirtualInterfaces()
        for port in self.ports:
            ifaceName = self.switch.name + '-' + self.__class__.type + '-eth' + str(port)
            os.system('ip link add name ' + ifaceName + ' type veth peer name ' + ifaceName + '-f')
            os.system('ifconfig ' + ifaceName + ' up')
            os.system('ifconfig ' + ifaceName + '-f' + ' up')

    def removeVirtualInterfaces(self):
        if len(self.switch.realIfaces[self.__class__]) > 0:
            return

        for port in self.ports:
            ifaceName = self.switch.name + '-' + self.__class__.type + '-eth' + str(port)
            os.system('ip link del ' + ifaceName)
            os.system('ip link del ' + ifaceName + '-f')

    def clean(self):
        self.stop()
        self.shell.stdin.close()
        self.shell.stdout.close()
        del self.shell
        
    def init(self):
        cmd = ['bash', '-m']
        self.shell = Popen( cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True )
#       self.pollOut = select.poll()
#       self.pollOut.register( self.shell.stdout )
        self.start()

    def getInterfaces(self): 
        ifaces = []
        for port in self.ports:
            ifaces.append(self.switch.name + '-' + self.__class__.type + '-eth' + str(port))
        return ifaces

    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError


class OpenFlowUserSwitch(VirtualSwitch):
    type = "rus"
    value = 300
    
    def start(self):
        ifaces = self.getInterfaces()
        ofdlog = '/tmp/' + self.switch.name + "_" + self.__class__.type + '-ofd.log'
        ofplog = '/tmp/' + self.switch.name + "_" + self.__class__.type + '-ofp.log'
        opts = ' --listen=ptcp:%i ' % (self.controller_port + 1 + self.openflow_id % 1000)
        mac_str = ' -d %.12X' % self.openflow_id

        self.runSwitchCmd( 'ofdatapath -v -i' + ','.join(ifaces) + ' punix:/tmp/' + self.switch.name + mac_str + ' --no-slicing ' + ' 1> ' + ofdlog + ' 2> ' + ofdlog + ' &')
        self.runSwitchCmd( 'ofprotocol -v unix:/tmp/' + self.switch.name + ' tcp:%s:%d' % ( self.controller_ip, self.controller_port ) + ' --fail=closed ' + opts + ' 1> ' + ofplog + ' 2>' + ofplog + ' &')

    def stop(self):
        self.runSwitchCmd( 'kill %ofdatapath ;' )
        self.runSwitchCmd( 'kill %ofprotocol ;' )

    def restart(self):
        pass


class OpenFlowKernelSwitch(VirtualSwitch):
    def start(self):
        ifaces = self.getInterfaces()
        dp = "nl:%i"%self.openflow_id
        ofplog = '/tmp/' + self.switch.name + '-ofp.log'
        opts = ' --listen=ptcp:%i ' % (self.controller_port + 1 + self.openflow_id % 1000)
        os.system('dpctl deldp ' + dp)
        os.system('dpctl adddp ' + dp)
        os.system('dpctl addif ' + dp + ' '.join(ifaces))
        self.runSwitchCmd( 'ofprotocol ' + dp + ' tcp:%s:%d' % ( self.controller_ip, self.controller_port ) + ' --fail=closed ' + opts + ' 1> ' + ofplog + ' 2>' + ofplog + ' &')

    def stop(self):
        dp = "nl:%i"%self.openflow_id
        os.system('dpctl deldp ' + dp)
        self.runSwitchCmd( 'kill %ofprotocol ;' )


class OVSSwitch(VirtualSwitch):
    type = "ovs"
    value = 200

    def start(self):
        ifaces = self.getInterfaces()
        ofplog = '/tmp/' + self.switch.name + "_" + self.__class__.type + '-ofp.log'
        dp = 'dp%i' % self.openflow_id
        opts = ' --listen=ptcp:%i ' % (self.controller_port + 1 + self.openflow_id)
        mac_str = '  --datapath-id=%.16X' % self.openflow_id
        os.system('ovs-dpctl del-dp ' + dp)
        os.system('ovs-dpctl add-dp ' + dp)
        os.system('ovs-dpctl add-if ' + dp + ' ' + ' '.join(ifaces))
        self.runSwitchCmd( 'ovs-openflowd ' + dp + ' tcp:%s:%d' % ( self.controller_ip, self.controller_port ) + ' --fail=secure ' + opts + mac_str + ' 1>' + ofplog + ' 2>' + ofplog + '&' )

    def stop(self):
        dp = 'dp%i' % self.openflow_id
        os.system('ovs-dpctl del-dp ' + dp )
        self.runSwitchCmd('kill %ovs-openflowd')


class HpSwitch(VirtualSwitch):
    type = "hp"
    value = 3294797090480896

    def __init__(self, switch, controller_ip, controller_port):
        VirtualSwitch.__init__(self, switch, controller_ip, controller_port)

#   def createVirtualInterfaces(self):
#       pass

#   def removeVirtualInterfaces(self):
#       pass

#   def getInterfaces(self):
#       return ["eth1", "eth2"]

    def start(self):
        pass
#       os.system('dpctl del-flows ' + ' tcp:%s:%d' % ( "128.178.149.200", (self.controller_port + 1 + 1) ) ) #self.switch.openflow_id) ) )
#       time.sleep(1)

    def stop(self):
        pass


