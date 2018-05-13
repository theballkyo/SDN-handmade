import time

from repository.repository import Repository


class DeviceNeighborRepository(Repository):
    def __init__(self):
        super(DeviceNeighborRepository, self).__init__()
        self.cdp = self.db.device_neighbor  # Todo deprecated
        self.model = self.db.device_neighbor

    def get_by_management_ip(self, management_ip):
        return self.model.find_one({'management_ip': management_ip})

    def update_neighbor(self, management_ip, neighbor):
        self.model.update_one({
            'management_ip': management_ip
        }, {
            '$set': {
                'management_ip': management_ip,
                'neighbor': neighbor,
                'updated_at': time.time()
            }
        }, upsert=True)
