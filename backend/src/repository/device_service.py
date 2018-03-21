import time

from service import BaseService


class DeviceService(BaseService):
    """ Device service
    """

    def __init__(self, *args, **kwargs):
        super(DeviceService, self).__init__(*args, **kwargs)
        self.device = self.db.device

    def get_device(self, management_ip):
        """ Get device object """
        return self.device.find_one({'management_ip': management_ip})

    def get_active(self):
        """ Get devices is active """
        return self.device.find({'active': True})

    def get_all(self):
        return self.device.find()

    def get_by_snmp_can_run(self, delay):
        return self.device.find({
            'snmp_is_running': False,
            'snmp_last_run_time': {
                '$lte': time.time() - delay
            }
        })

    def set_snmp_running(self, management_ip, is_running):
        self.device.update_one({
            'management_ip': management_ip
        }, {
            '$set': {
                'snmp_is_running': is_running
            }
        })

    def set_snmp_finish_running(self, management_ip):
        self.device.update_one({
            'management_ip': management_ip
        }, {
            '$set': {
                'snmp_is_running': False,
                'snmp_last_run_time': time.time()
            }
        })

    def snmp_is_running(self, management_ip):
        device = self.device.find_one({
            'management_ip': management_ip
        })
        if device is None:
            return True
        return device.get('snmp_is_running', False)

    def get_ssh_info(self, management_ip):
        data = self.db.device.find_one({
            'management_ip': management_ip
        })
        if data is None:
            return None
        ssh_info = data['ssh_info']
        ssh_info['ip'] = management_ip
        ssh_info['device_type'] = data['type']
        return ssh_info

    def find_by_if_ip(self, ip):
        """
        """
        return self.device.find_one({
            'interfaces.ipv4_address': ip
        })

    def get_if_ip_by_if_index(self, management_ip, index):

        query = self.device.aggregate([
            {'$unwind': 'interfaces'},
            {'$match': {'management_ip': management_ip, 'interfaces.index': index}},
            {'$project': {'interfaces.ipv4_address': 1}}
        ])
        if query is None:
            return None
        return query['ipv4_address']

    def get_interface_by_ip(self, interface_ip):

        query = self.device.find_one({
            'interfaces.ipv4_address': interface_ip
        }, {
            'management_ip': 1,
            'interfaces.$': 1
        })

        if query is None:
            return None

        device = {
            'management_ip': query['management_ip'],
            'interface': query['interfaces'][0]
        }

        return device

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

    def increase_offline_count(self, management_ip):
        """ Update offline count by increase by 1
        """
        self.device.update_one({
            'management_ip': management_ip
        }, {
            '$inc': {
                'mark_offline_count': 1
            }
        })

    def remove(self, management_ip):
        """ Remove device """
        self.device.remove({'management_ip': management_ip})

    def get_by_if_utilization(self, percent, side='in'):
        if side == 'in':
            key_name = 'bw_in_usage_percent'
        elif side == 'out':
            key_name = 'bw_out_usage_percent'
        else:
            raise ValueError('side can be only in or out')

        return self.device.find({
            'interfaces.' + key_name: {
                '$gte': percent
            }
        }, {
            'management_ip': 1,
            'interfaces.$': 1
        })
