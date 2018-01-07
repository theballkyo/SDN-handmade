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
    # logging.debug(subnet_dict)
    # for subnet in subnet_dict:
    #     net = subnet_dict[subnet]
    #     logging.debug("Subnet\t{}".format(subnet))
    #     for n in net:
    #         logging.debug("\tIP: {}\tDevice: {}".format(n['ip'], n['device_name']))
    #
    # # Matrix subnet
    # subnet_matrix = []
    # # print(subnet_dict)
    #
    # for src_subnets in subnet_dict:
    #     for src_subnet in subnet_dict[src_subnets]:
    #         for dst_subnets in subnet_dict:
    #             for dst_subnet in subnet_dict[dst_subnets]:
    #                 if src_subnet['ip'] == dst_subnet['ip'] and \
    #                     src_subnets == dst_subnets:
    #                     continue
                    # print(src_subnets, dst_subnets)
    # for subnet in subnet_dict:
    #     matrix = {
    #         'subnet': subnet,
    #         'to': []
    #     }
    #     for subnet2 in subnet_dict:
    #         if subnet == subnet2:
    #             continue
    #         # print(subnet, subnet2)
    #         matrix['to'].append({
    #             'subnet': subnet2,
    #             'routes': [{
    #                 # 'start_at': subnet_dict[subnet]['device'],
    #                 'start_at': '...',
    #                 'route': '1, 0, 1, 1, 1',
    #                 'end_at': '...'
    #                 # 'end_at': subnet_dict[subnet2]['device']
    #             }],
    #             # Extra infomation ....
    #         })
    #     subnet_matrix.append(matrix)
    # print(subnet_matrix)

if __name__ == '__main__':
    create_subnet(exclude_ips=[('192.168.106.0', '255.255.255.0')])
