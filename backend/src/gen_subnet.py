# import copy
import ipcalc
import logging

from database import MongoDB


class Subnet:
    def __init__(self, network):
        # self.devices = []
        self.network = None

    def __str__(self):
        return self.network


def create_subnet(devices, exclude_ips=None):
    """ Create subnet
    """
    num_device = len(devices)

    subnet_dict = {}
    for n1 in range(num_device):
        for interface in devices[n1].get_interfaces():
            # print(interface)
            device = devices[n1]
            ip = interface.get('ipv4_address')
            if not ip:
                continue
            mask = interface['subnet']
            network = ipcalc.Network(ip, mask)
            # print(network.network())
            network_str = "{}/{}".format(network.network(), network.subnet())
            # print(network_str)
            if not subnet_dict.get(network_str):
                subnet_dict[network_str] = []

            subnets = subnet_dict.get(network_str)
            subnet_info = {
                'device_name': devices[n1].get_name(),
                'ip': ip
            }

            subnets.append(subnet_info)

            device.subnets[network_str] = {
                'ip': ip
            }
            # print(network_str, subnets)
    return subnet_dict


if __name__ == '__main__':
    create_subnet(exclude_ips=[('192.168.106.0', '255.255.255.0')])
