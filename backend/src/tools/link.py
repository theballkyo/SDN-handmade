import netaddr
from repository import get_service


class Link:
    def __init__(self, src_ip, dst_ip, src_node=None, dst_node=None):
        if src_ip == dst_ip:
            raise ValueError()

        if netaddr.IPAddress(src_ip) < netaddr.IPAddress(dst_ip):
            self.src_ip = src_ip
            self.dst_ip = dst_ip
        else:
            self.src_ip = dst_ip
            self.dst_ip = src_ip

        self.src_if = None
        self.src_node = None

        self.dst_if = None
        self.dst_node = None

    def _fetch_info(self):
        device_service = get_service('device')
        links = device_service.device.find({
            'interfaces.ipv4_address': {
                '$in': [
                    self.src_ip, self.dst_ip
                ]
            }
        }, {
            'management_ip': 1,
            'interfaces.$1': 1
        })

        for link in links:
            if link['interfaces'][0]['ipv4_address'] == self.src_ip:
                self.src_node = link['management_ip']
                self.src_if = link['interfaces'][0]
            else:
                self.dst_node = link['management_ip']
                self.dst_if = link['interfaces'][0]

    def info(self, fetch=True):
        if fetch or self.src_if is None or self.dst_if is None:
            self._fetch_info()

    @staticmethod
    def link_info(src_ip, dst_ip):
        #
        # if link['src']['management_ip'] == path[i]:
        #     out_if = link['src']['interfaces'][0]
        #     in_if = link['dst']['interfaces'][0]
        # else:
        #     out_if = link['dst']['interfaces'][0]
        #     in_if = link['src']['interfaces'][0]
        #
        # out_available = out_if['speed'] - (out_if['bw_in_usage_percent'] / 100 * out_if['speed'])
        # in_available = in_if['speed'] - (in_if['bw_in_usage_percent'] / 100 * in_if['speed'])
        pass
