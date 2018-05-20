import logging

from repository.repository import Repository
import pprint


class FlowStatRepository(Repository):
    def __init__(self, *args, **kwargs):
        super(FlowStatRepository, self).__init__(*args, **kwargs)
        self.netflow = self.db.flow_stat  # Todo Deprecated in next version
        self.model = self.db.flow_stat  # Use this

    def insert_many(self, data):
        # pprint.pprint(data)
        self.model.insert_many(data)

    def get_ingress_flow(self, start_time, end_time, limit=10, skip=0, addition_match=None, group_by=(),
                         sort=None, side='ingress'):
        """
        Getting flow
        :param start_time: First switched time >= start time
        :param end_time:  First switched time <= end time
        :param limit: Limit flow
        :param skip: Skip
        :param addition_match: Addition match filter
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

        if addition_match:
            match = {**match, **addition_match}
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
        flows = self.model.aggregate(pipeline)
        return flows

    def summary_flow(self, from_ip, start_datetime, direction=0):
        match_1 = {
            'from_ip': from_ip,
            'direction': direction
        }
        project_1 = {
            'from_ip': 1,
            'first_switched': 1,
            'last_switched': 1,
            'ipv4_src_addr': 1,
            'ipv4_dst_addr': 1,
            'in_bytes_per_sec': {
                '$cond': [
                    {'$eq': ['$in_pkts', 1]},
                    '$in_bytes',
                    {'$divide': [
                        '$in_bytes',
                        {'$divide': [
                            {'$subtract': ["$last_switched", "$first_switched"]},
                            1000]}
                    ]}
                ]
            },
            'total_in_bytes': {
                '$cond': [
                    {  # In time range
                        '$gte': ['$first_switched', start_datetime]
                    },
                    '$in_bytes',
                    {  # Case flow start before start_datetime
                        '$multiply': [{  # total_time * in_bytes_per_sec
                            '$divide': [  # Total time
                                {'$subtract': ['$last_switched', start_datetime]},
                                1000
                            ]
                        }, {
                            '$cond': [  # In bytes per seconds
                                {'$eq': [{'$subtract': ["$last_switched", "$first_switched"]}, 0]},
                                '$in_bytes',
                                {'$divide': [
                                    '$in_bytes',
                                    {
                                        '$divide': [
                                            {'$subtract': ["$last_switched", "$first_switched"]},
                                            1000]
                                    }
                                ]}
                            ]
                        }]
                    }
                ]
            },
            'total_in_pkts': {
                '$cond': [
                    {  # In time range
                        '$gte': ['$first_switched', start_datetime]
                    },
                    '$in_pkts',
                    {  # Case flow start before start_datetime
                        '$multiply': [{  # total_time * in_bytes_per_sec
                            '$divide': [  # Total time
                                {'$subtract': ['$last_switched', start_datetime]},
                                1000
                            ]
                        }, {
                            '$cond': [  # In bytes per seconds
                                {'$eq': [{'$subtract': ["$last_switched", "$first_switched"]}, 0]},
                                '$in_pkts',
                                {'$divide': [
                                    '$in_pkts',
                                    {
                                        '$divide': [
                                            {'$subtract': ["$last_switched", "$first_switched"]},
                                            1000]
                                    }
                                ]}
                            ]
                        }]
                    }
                ]
            },
            'in_pkts': 1,
            'in_bytes': 1

        }

        match_2 = {
            'total_in_bytes': {'$gte': 0}
        }

        group = {
            '_id': {
                'ipv4_src_addr': "$ipv4_src_addr",
                'ipv4_dst_addr': "$ipv4_dst_addr"

            },
            'total_in_bytes': {'$sum': "$total_in_bytes"},
            'total_in_pkts': {'$sum': '$total_in_pkts'}
        }

        sort = {
            'total_in_bytes': -1
        }

        return self.model.aggregate([
            {'$match': match_1}, {'$project': project_1}, {'$match': match_2}, {'$group': group}, {'$sort': sort}
        ])

    def summary_flow_v2(self, from_ip, not_in=None):
        match = {
            'from_ip': from_ip
        }
        if not_in:
            # match['$or'] = [
            #     {'ipv4_src_addr': {
            #         '$nin': not_in['src_ip']
            #     }},
            #     # {'l4_src_port': {
            #     #     '$nin': not_in['src_port']
            #     # }},
            #     {'ipv4_dst_addr': {
            #         '$nin': not_in['dst_ip']
            #     }},
            #     # {'ipv4_dst_port': {
            #     #     '$nin': not_in['dst_port']
            #     # }}
            # ]
            match['$and'] = not_in
        logging.info(pprint.pformat(match))
        return self.model.aggregate([
            {'$match': match},
            {'$group': {
                '_id': {  # Currently ignore port, proto
                    # Todo support port, protocol
                    "ipv4_src_addr": "$ipv4_src_addr",
                    "ipv4_dst_addr": "$ipv4_dst_addr",
                    "l4_src_port": "$l4_src_port",
                    "l4_dst_port": "$l4_dst_port"
                },
                'in_bytes': {'$sum': '$in_bytes'},
                'in_pkts': {'$sum': '$in_pkts'},
                'in_bytes_per_sec': {'$sum': {
                    '$cond': [
                        {'$eq': [{'$subtract': ['$last_switched', '$first_switched']}, 0]},
                        '$in_bytes',
                        {'$divide': ['$in_bytes', {
                            '$divide': [{'$subtract': ['$last_switched', '$first_switched']}, 1000]}]}
                    ]
                }},
                'in_pkts_per_sec': {'$sum': {
                    '$cond': [
                        {'$eq': [{'$subtract': ['$last_switched', '$first_switched']}, 0]},
                        '$in_pkts',
                        {'$divide': ['$in_pkts', {
                            '$divide': [{'$subtract': ['$last_switched', '$first_switched']}, 1000]}]}
                    ]
                }}
                # 'count_src_port': {'$count': '$l4_src_port'}
            }},
            {
                '$sort': {
                    'in_bytes_per_sec': -1
                }
            }
        ])

    def get_flows(self, sort_by='in_bytes', limit=1):
        return self.model.find().sort({sort_by: -1}).limit(limit)

    def update_flows(self, flows):
        not_keys = ('first_switched', 'last_switched', 'in_bytes', 'in_pkts', 'out_bytes', 'out_pkts', 'created_at')
        for flow in flows:
            _flow = flow.copy()
            for key in not_keys:
                try:
                    _flow.pop(key)
                except KeyError:
                    pass

            self.model.update_one(
                _flow,
                # {
                #     'ipv4_src_addr': flow['ipv4_src_addr'],
                #     'ipv4_dst_addr': flow['ipv4_dst_addr'],
                #     'protocol': flow['protocol'],
                #     'l4_src_port': flow['l4_src_port'],
                #     'l4_dst_port': flow['l4_dst_port'],
                # 'src_mask': flow['src_mask'],
                # 'dst_mask': flow['dst_mask'],
                # 'input_snmp': flow['input_snmp'],
                # 'output_snmp': flow['output_snmp'],
                # 'src_as': flow['src_as'],
                # 'dst_as': flow['dst_as'],
                # 'ipv4_next_hop': flow['ipv4_netx_hop'],
                #
                # 'src_tos': flow['src_tos'],
                # 'tcp_flags': flow['tcp_flags'],
                # 'from_ip': flow['from_ip'],
                # 'direction': flow['direction']
                # }, {
                {
                    '$set': flow
                }, upsert=True)

    def is_flow_exist_by_ip(self, src_ip, dst_ip):
        return self.model.find_one({
            'ipv4_src_addr': src_ip,
            'ipv4_dst_addr': dst_ip
        })

    def get_all(self, **kwargs):
        return self.model.find(**kwargs).sort("from_ip", 1)
