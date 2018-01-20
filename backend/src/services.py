from database import get_mongodb


class Service:
    def __init__(self, *args, **kwargs):
        self.mongodb = get_mongodb()
        self.db = self.mongodb.db


class AppService(Service):
    def __init__(self, *args, **kwargs):
        super(AppService, self).__init__(*args, **kwargs)

    def is_running(self):
        app = self.db.app.find_one({}, {'is_running': 1})
        return app

    def set_running(self, running):
        self.db.app.update_one({}, {
            '$set': {
                'is_running': running
            }
        })


class CdpService(Service):
    def __init__(self, *args, **kwargs):
        super(CdpService, self).__init__(*args, **kwargs)

    def get_by_management_ip(self, management_ip):
        return self.db.cdp.find_one({'management_ip': management_ip})


class DeviceService(Service):
    """ Device service
    """

    def __init__(self, *args, **kwargs):
        super(DeviceService, self).__init__(*args, **kwargs)
        self.device = self.db.device

    def get_device(self, management_ip):
        """ Get device object """
        return self.device.find({'management_ip': management_ip})

    def get_active(self):
        """ Get devices is active """
        return self.device.find({'active': True})

    def find_by_if_ip(self, ip):
        """
        """
        return self.device.find_one({
            'interfaces.ipv4_address': ip
        })

    def add_device(self, device):
        """ Add device """
        if device.get('management_ip') is None:
            raise ValueError('Device dict must be `management_ip` key')

        snmp_info = device.get('snmp_info')
        if snmp_info is None:
            raise ValueError('SNMP must be not None')
        if snmp_info.get('community') is None:
            raise ValueError()
        if snmp_info.get('port') is None:
            raise ValueError()

        self.device.update_one({
            'management_ip': device.get('management_ip'),
        }, {
            '$set': device
        }, upsert=True)

    def remove(self, management_ip):
        """ Remove device """
        self.device.remove({'management_ip': management_ip})


# Prepare to create a objects
app_service = AppService()
cdp_service = CdpService()
device_service = DeviceService()
