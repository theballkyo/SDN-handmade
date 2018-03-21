from repository.base_service import BaseService
from pymongo import UpdateOne


class TopologyService(BaseService):
    def __init__(self):
        super(TopologyService, self).__init__()
        self.topology = self.db.topology

    def add_subnet_to_subnet(self, info):
        self.topology.update_one({
            'from_subnet': info['from_subnet'],
            'to_subnet': info['to_subnet']
        }, {
            '$set': info
        }, upsert=True)

    def add_subnet_to_subnet_bulk(self, info_bulk):
        insert_list = []
        for info in info_bulk:
            insert_list.append(UpdateOne({
                'from_subnet': info['from_subnet'],
                'to_subnet': info['to_subnet']
            }, {
                '$set': info
            }, upsert=True))

        self.topology.bulk_write(insert_list)
