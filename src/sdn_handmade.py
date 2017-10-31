from snmp_worker import SNMPWorker
from netflow import NetflowWorker
from gen_nb import get_neighbor


class Route:
    def __init__(self):
        pass


class Device:
    def __init__(self, ip, snmp_community='public'):
        self.ip = ip
        self.snmp_community = snmp_community


class Router(Device):
    def __init__(self, ip, snmp_community='public'):
        super(Router, self).__init__(ip, snmp_community)


class Topoloygy:
    def __init__(self, netflow_ip='127.0.0.1', netflow_port=23456):
        self.devices = []
        self.subnets = []

        self._snmp_worker = SNMPWorker()

        self._netflow_worker = NetflowWorker(
            netflow_ip,
            netflow_port
        )

    def run(self):
        """ Start topoloygy loop
        """
        self._netflow_worker.start()
        self._snmp_worker.run()

    def get_neighbor(self):
        return get_neighbor()

    def add_device(self, devices):
        """ Add device(s) to topoloygy
        """
        if isinstance(devices, list):
            for device in devices:
                self._add_device(device)
        else:
            self._add_device(devices)

    def _add_device(self, device):
        if not isinstance(device, Device):
            print("device argument is not instance of Device")
            return
        self.devices.append(Device)
        # Add to snmp worker
        self._snmp_worker.add_device(device.ip, device.snmp_community)
