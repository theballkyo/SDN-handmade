import services

if __name__ == '__main__':
    device_service = services.get_service('device')
    devices = device_service.get_all()
    for device in devices:
        device_service.set_snmp_running(device['management_ip'], False)
