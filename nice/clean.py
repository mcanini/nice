from subprocess import Popen, PIPE

def sh(cmd):
    return Popen( [ '/bin/sh', '-c', cmd ], stdout=PIPE ).communicate()[ 0 ]

def cleanup():
    zombies = 'controller ofprotocol ofdatapath ping nox_core lt-nox_core '
    zombies += 'ovs-openflowd udpbwtest'
    # Note: real zombie processes can't actually be killed, since they
    # are already (un)dead. Then again,
    # you can't connect to them either, so they're mostly harmless.
    sh( 'killall -9 ' + zombies + ' 2> /dev/null' )
    sh( 'killall nice.py')

    sh( 'rm -f /tmp/vconn* /tmp/vlogs* /tmp/*.out /tmp/*.log' )

    dps = sh( "ps ax | egrep -o 'dp[0-9]+' | sed 's/dp/nl:/'" ).split( '\n' )
    for dp in dps:
        if dp != '':
            sh( 'dpctl deldp ' + dp )

    links = sh( "ip link show | egrep -o '(\w+-\w+-eth\w+-f)'" ).split( '\n' )
    print links
    for link in links:
        if link != '':
            sh( "ip link del " + link )

cleanup()

