from .sdn_cmd import SDNCommand


class DeviceCommand(SDNCommand):
    def __init__(self, topology, logbug):
        super(DeviceCommand, self).__init__()
        self.topology = topology
        self.logbug = logbug
        self.prompt = 'SDN Handmade (0.0.1)(config)# '

    def do_aaa(self, args):
        """

        :param args:
        :return:
        """
        print("From device cmd")
