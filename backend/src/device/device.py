import logging
import sdn_utils


class Device:
    """ Device object
    """

    STATUS_OFFLINE = 0
    STATUS_ONLINE = 1
    STATUS_MARK_OFFLINE = 2

    DEVICE_STATUS = (
        (STATUS_OFFLINE, 'Offline'),
        (STATUS_ONLINE, 'Online'),
        (STATUS_MARK_OFFLINE, 'Mark offline'),
    )

    def __init__(self, device_info, ssh_info, snmp_info):
        self.ip = device_info['ip']

        self.ssh_info = ssh_info
        self.ssh_info['ip'] = self.ip

        self.snmp_info = snmp_info

        self.type = 'device'

        # Default status
        self.status = self.STATUS_OFFLINE

        self.info = {}

        self.neighbor = []
        self.route = []
        self.subnet_list = {}

    def set_status(self, status):
        """ Set device status """
        # TODO
        verify = False
        for _status in self.DEVICE_STATUS:
            if _status[0] == status:
                verify = True
                break

        if not verify:
            logging.info("Can't find device status ID {}", status)
            return

        self.init_device()
        self.info['status'] = status
        # Reset mark offline count
        if status == self.STATUS_ONLINE:
            self.info['mark_offline_count'] = 0

    def mark_offline(self):
        # TODO
        # device service increase_offline_count
        raise NotImplementedError

    def get_status(self):
        self.init_device()
        return self.info['status']

    def init_device(self):
        """ Initialize device
        """
        info = self.mongo.device.find_one({
            'device_ip': self.ip
        })

        if info is None:
            self.mongo.device.insert_one({
                'device_ip': self.ip,
                'status': self.STATUS_OFFLINE,
                'mark_offline_count': 0
            })

            info = self.mongo.device.find_one({
                'device_ip': self.ip
            })

        self.info = info

    def query(self, field, default=None):
        self.init_device()
        return self.info.get(field, default)

    def get_name(self):
        """ Get device name
        """
        return self.query('name', 'Unknown')

    def get_interfaces(self):
        """ Get interfaces of device
        """
        return self.query('interfaces', [])

    def get_info(self):
        self.init_device()
        return self.info

    def get_cdp(self):
        return self.mongo.cdp.find_one({'device_ip': self.ip})

    def find_neighbor_by_name(self, name):
        """ Find neighbor by device name
            and return Device object
        """
        for device in self.neighbor:
            if device.get_name() == name:
                return device
        return None

    def find_neighbor(self, other_device):
        """ Find neighbor by device name
            and return Device object
        """
        for link_info in self.neighbor:
            if other_device == link_info['neighbor_obj']:
                return link_info
        return None

    def get_routes(self):
        """ Get routes
        """
        self.init_device()
        self.route = self.mongo.route.find({'device_ip': self.ip}).sort([
            ('ipCidrRouteDest', self.mongo.pymongo.ASCENDING),
            ('ipCidrRouteMask', self.mongo.pymongo.DESCENDING)
        ])

        return self.route

    def uptime(self):
        _time = self.query('uptime')
        if not _time:
            return "Down"
        return sdn_utils.millis_to_datetime(_time * 10)

    def information_text(self):
        """ Display device information
        """
        self.init_device()
        return "{} ({}) uptime - {}".format(self.get_name(),
                                            self.ip,
                                            self.uptime())

    def __repr__(self):
        self.init_device()
        return "{}".format(self.get_name())

    def __str__(self):
        self.init_device()
        return "{}".format(self.get_name())
