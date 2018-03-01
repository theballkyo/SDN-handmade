from service import BaseService
import logging


class NetflowService(BaseService):
    def __init__(self, *args, **kwargs):
        super(NetflowService, self).__init__(*args, **kwargs)
        self.netflow = self.db.netflow

    def insert_many(self, data):
        self.netflow.insert_many(data)

    def get_ingress_flow(self, start_time, end_time, limit=10, skip=0, extra_match=None, group_by=(),
                         sort=None, side='ingress'):
        """
        Getting flow
        :param start_time: First switched time >= start time
        :param end_time:  First switched time <= end time
        :param limit: Limit flow
        :param skip: Skip
        :param extra_match: Extra match filter
        :param group_by: Group by default use 4 fields
        :param sort: Sort by default sort by total_in_bytes
        :param side: Side flow can be only ingress, egress and all
        :return:
        """

        # Match stage
        match = {
            'first_switched': {
                '$gte': start_time,
                '$lte': end_time
            }
        }

        if extra_match:
            match = {**match, **extra_match}
            # print(match)

        # Group stage
        group = {
            '_id': {}
        }

        if side == 'ingress' or side == 'all':
            group['total_in_bytes'] = {'$sum': '$in_bytes'}
            group['total_in_pkts'] = {'$sum': '$in_pkts'}
        if side == 'egress' or side == 'all':
            group['total_out_bytes'] = {'$sum': '$out_bytes'}
            group['total_out_pkts'] = {'$sum': '$out_pkts'}

        if len(group_by) == 0:
            group_by = ('ipv4_src_addr', 'ipv4_dst_addr', 'l4_src_port', 'l4_dst_port', 'input_snmp')

        for field in group_by:
            group['_id'][field] = '$' + field  # Add $ before field name

        # Sort stage
        if not sort:
            if side == 'ingress' or side == 'all':
                sort = {
                    'total_in_bytes': -1
                }
            if side == 'egress' or side == 'all':
                sort = {
                    'total_out_bytes': -1
                }

        # Add total flow count stage
        count_flow = {
            "_id": None,
            "total_flow": {
                "$sum": 1
            },
            "data": {
                "$push": {
                    "_id": "$_id",
                }
            }
        }
        if side == 'ingress' or side == 'all':
            count_flow["data"]["$push"]["total_in_bytes"] = "$total_in_bytes"
            count_flow["data"]["$push"]["total_in_pkts"] = "$total_in_pkts"

        if side == 'egress' or side == 'all':
            count_flow["data"]["$push"]["total_out_bytes"] = "$total_out_bytes"
            count_flow["data"]["$push"]["total_out_pkts"] = "$total_out_pkts"

        pipeline = [{'$match': match}, {'$group': group}, {'$sort': sort}, {'$skip': skip},
                    {'$limit': limit}, {'$group': count_flow}]

        logging.debug(pipeline)
        flows = self.netflow.aggregate(pipeline)
        return flows
