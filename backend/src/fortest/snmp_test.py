from pysnmp.hlapi import *
i = 0
oid = "1.3.6.1.2.1.2"
# 1.3.6.1.2.1.4.24
for (errorIndication,
     errorStatus,
     errorIndex,
     varBinds) in nextCmd(SnmpEngine(),
                          CommunityData('public'),
                          UdpTransportTarget(('demo.snmplabs.com', 161)),
                          ContextData(),
                          ObjectType(ObjectIdentity(oid))):

    # if i % 100 == 0:
    #   print(varBinds[0][0].getOid())
    #   break
    # i += 1

    if not str(varBinds[0][0].getOid()).startswith(oid):
        break

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
