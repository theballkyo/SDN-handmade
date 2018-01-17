from database import get_connection


class AppService:
    def __init__(self, *args, **kwargs):
        self.mongo = get_connection()
        self.db = self.mongo.db

    def is_running(self):
        app = self.db.app.find_one({}, {'is_running': 1})
        return app

    def set_running(self, running):
        self.db.app.update_one({}, {
            '$set': {
                'is_running': running
            }
        })


class CdpService:
    def __init__(self, *args, **kwargs):
        self.mongo = get_connection()
        self.db = self.mongo.db

    def get_by_mangement_ip(self, management_ip):
        return self.db.cdp.find_one({'management_ip': management_ip})


class DeviceService:
    ''' Device service '''

    def __init__(self):
        self.db = get_connection()
        self.collection = self.db.device

    def get_device(self, management_ip):
        ''' Get device object '''
        return self.collection.find({'management_ip': management_ip})

    def get_active(self):
        ''' Get devices is active '''
        return self.collection.find({'active': True})

    def find_by_if_ip(self, ip):
        """
        """
        return self.collection.find_one({
            'interfaces.ipv4_address': ip
        })

    def add_device(self, device):
        ''' Add device '''
        if device.get('management_ip') is None:
            raise ValueError('Device dict must be `management_ip` key')

        snmp_info = device.get('snmp_info')
        if snmp_info is None:
            raise ValueError('SNMP must be not None')
        if snmp_info.get('community') is None:
            raise ValueError()
        if snmp_info.get('port') is None:
            raise ValueError()

        self.collection.update_one({
            'management_ip': device.get('management_ip'),
        }, {
            '$set': device
        }, upsert=True)

    def remove(self, management_ip):
        ''' Remove device '''
        self.collection.remove({'management_ip': management_ip})
