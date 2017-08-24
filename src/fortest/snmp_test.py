from pysnmp.hlapi import *
i = 0
for (errorIndication,
     errorStatus,
     errorIndex,
     varBinds) in nextCmd(SnmpEngine(),
                          CommunityData('public'),
                          UdpTransportTarget(('192.168.122.2', 161)),
                          ContextData(),
                          ObjectType(ObjectIdentity('.1.3.6.1.2.1.4.24'))):

    if i > 100:
      print(type(varBinds[0]))
      break
    i += 1

    if errorIndication:
        print(errorIndication)
        break
    elif errorStatus:
        print('%s at %s' % (errorStatus.prettyPrint(),
                            errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
        break
    else:
        for varBind in varBinds:
            print(' = '.join([x.prettyPrint() for x in varBind]))