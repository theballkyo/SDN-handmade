from service.base_service import BaseService
from pymongo import UpdateOne
import netaddr


class LinkService(BaseService):
    def __init__(self):
        super(LinkService, self).__init__()
        self.link = self.db.link

    def add_links(self, links):
        ops = []
        for link in links:
            ops.append(
                UpdateOne({
                    'src_node_ip': link['src_node_ip'],
                    'dst_node_ip': link['dst_node_ip']
                }, {
                    '$set': {
                        'src_node_ip': link['src_node_ip'],
                        'dst_node_ip': link['dst_node_ip'],
                        'src_if_ip': link['src_if_ip'],
                        'dst_if_ip': link['dst_if_ip'],
                        'src_if_index': link['src_if_index'],
                        'dst_if_index': link['dst_if_index'],
                    }
                }, upsert=True)
            )
        self.link.bulk_write(ops)

    def find_by_if_ip(self, ip1, ip2=None):
        if ip2 is None:
            links = self.link.find({
                '$or': [
                    {'src_if_ip': ip1},
                    {'dst_if_ip': ip1}
                ]
            })
            return links

        ip1 = netaddr.IPAddress(ip1)
        ip2 = netaddr.IPAddress(ip2)

        if ip1 > ip2:
            ip1, ip2 = ip2, ip1

        link = self.link.find_one({
            'src_if_ip': str(ip1),
            'dst_if_ip': str(ip2)
        })
        return link

    def find_by_if_index(self, mgmt_ip, index):
        link = self.link.find({
            '$or': [
                {'src_node_ip': mgmt_ip, 'src_if_index': index},
                {'dst_node_ip': mgmt_ip, 'dst_if_index': index}
            ]
        })
        return link
