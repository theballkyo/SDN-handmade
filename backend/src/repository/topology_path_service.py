from time import time

from repository.base_service import BaseService
from pymongo import UpdateOne


class TopologyPathService(BaseService):
    def __init__(self):
        super(TopologyPathService, self).__init__()
        self.topology_path = self.db.topology_path

    def add_new_path(self, path):
        self.topology_path.update_one({}, {'$set': path}, upsert=True)

    def insert_new_paths(self, paths):
        _insert = []
        for path in paths:
            _insert.append(UpdateOne({
                'path': list(path)
            }, {
                '$set': {
                    'from': path[0],
                    'to': path[-1],
                    'path': list(path),
                    'updated_at': time(),
                    'used': 100
                }
            }, upsert=True))

        self.topology_path.bulk_write(_insert)
