import time

from bson.objectid import ObjectId, InvalidId

from repository.repository import Repository


class DeviceRepository(Repository):
    """ Device repository
    """

    STATUS_ACTIVE = 1

    STATUS_WAIT_REMOVE = -1
    STATUS_WAIT_UPDATE = 2

    def __init__(self, *args, **kwargs):
        super(DeviceRepository, self).__init__(*args, **kwargs)
        self.device = self.db.device  # Todo Deprecated
        self.model = self.db.device

    @staticmethod
    def project_simple():
        return {
            'type': 1,
            'device_ip': 1,
            'description': 1,
            'management_ip': 1,
            'interfaces': 1
        }

    def get_device_by_mgmt_ip(self, management_ip):
        """ Get device object """
        return self.model.find_one({'management_ip': management_ip})

    def get_device_by_id(self, _id):
        return self.model.find_one({'_id': ObjectId(_id)})

    def get_by_id(self, _id):
        return self.model.find_one({'_id': ObjectId(_id)})

    def get_active(self):
        """ Get devices is active """
        return self.model.find({'active': True})

    def get_all(self):
        return self.model.find()

    def get_by_snmp_can_run(self, delay):
        return self.model.find({
            'snmp_is_running': False,
            'snmp_last_run_time': {
                '$lte': time.time() - delay
            }
        })

    def set_snmp_running(self, management_ip, is_running):
        self.model.update_one({
            'management_ip': management_ip
        }, {
            '$set': {
                'snmp_is_running': is_running
            }
        })

    def set_snmp_finish_running(self, management_ip):
        self.model.update_one({
            'management_ip': management_ip
        }, {
            '$set': {
                'snmp_is_running': False,
                'snmp_last_run_time': time.time()
            }
        })

    def set_cdp_by_mgmt_ip(self, management_ip: str, is_enable: bool):
        return self.model.update_one({
            'management_ip': management_ip
        }, {
            '$set': {
                'cdp_enable': is_enable
            }
        })

    def set_status_wait_remove(self, device_id: str):
        try:
            device_id = ObjectId(device_id)
        except InvalidId:
            return False

        return self.model.update_one({
            "_id": device_id
        }, {"$set": {
            "status": DeviceRepository.STATUS_WAIT_REMOVE
        }})

    def set_information(self, device_id: str, information: dict):
        try:
            device_id = ObjectId(device_id)
        except InvalidId:
            return False

        return self.model.update_one({
            "_id": device_id
        }, {"$set": {
            "ssh_info": information["ssh_info"],
            "snmp_info": information["snmp_info"],
            "type": information["type"],
            "status": DeviceRepository.STATUS_WAIT_UPDATE
        }})

    def set_ssh_is_connect_by_mgmt_ip(self, management_ip: str, is_connect: bool):
        self.model.update_one({
            "management_ip": management_ip
        }, {"$set": {
            "is_ssh_connect": is_connect
        }})

    def set_snmp_is_connect_by_mgmt_ip(self, management_ip: str, is_connect: bool):
        self.model.update_one({
            "management_ip": management_ip
        }, {"$set": {
            "is_snmp_connect": is_connect
        }})

    def set(self, management_ip: str, system_info: dict):
        return self.model.update_one({
            'management_ip': management_ip
        }, {
            '$set': system_info
        }, upsert=True)

    def snmp_is_running(self, management_ip):
        device = self.model.find_one({
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

    def find_by_if_ip(self, ip, project=None):
        """
        """
        if project is None:
            return self.model.find_one({
                'interfaces.ipv4_address': ip
            })
        return self.model.find_one({
            'interfaces.ipv4_address': ip
        }, project)

    def get_if_ip_by_if_index(self, management_ip, index):

        query = self.model.aggregate([
            {'$unwind': 'interfaces'},
            {'$match': {'management_ip': management_ip, 'interfaces.index': index}},
            {'$project': {'interfaces.ipv4_address': 1}}
        ])
        if query is None:
            return None
        return query['ipv4_address']

    def get_interface_by_ip(self, interface_ip):

        query = self.model.find_one({
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

        device['snmp_is_running'] = False
        device['snmp_last_run_time'] = 0

        self.model.update_one({
            'management_ip': device.get('management_ip'),
        }, {
            '$set': device
        }, upsert=True)

    def increase_offline_count(self, management_ip):
        """ Update offline count by increase by 1
        """
        self.model.update_one({
            'management_ip': management_ip
        }, {
            '$inc': {
                'mark_offline_count': 1
            }
        })

    def remove(self, management_ip):
        """ Remove device """
        self.model.remove({'management_ip': management_ip})

    def get_by_if_utilization(self, percent, side='in', cond='$gte'):
        if side == 'in':
            key_name = 'bw_in_usage_percent'
        elif side == 'out':
            key_name = 'bw_out_usage_percent'
        else:
            raise ValueError('side can be only in or out')

        return self.model.find({
            'interfaces.' + key_name: {
                cond: percent
            }
        }, {
            'type': 1,
            'snmp_info': 1,
            'management_ip': 1,
            'interfaces': 1
        }).sort([('interfaces.' + key_name, -1)])

    def get_device_type(self, management_ip):
        device = self.model.find_one({
            'management_ip': management_ip
        }, {'type': 1})

        return device['type']

    def get_device_type_by_id(self, _id):
        device = self.model.find_one({
            "_id": ObjectId(_id)
        }, {'type': 1})

        return device['type']
