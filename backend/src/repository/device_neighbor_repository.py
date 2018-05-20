from bson.objectid import ObjectId, InvalidId
from repository.repository import Repository
import sdn_utils


class DeviceNeighborRepository(Repository):
    def __init__(self):
        super(DeviceNeighborRepository, self).__init__()
        self.cdp = self.db.device_neighbor  # Todo deprecated
        self.model = self.db.device_neighbor

    def get_by_device_id(self, device_id: str):
        return self.model.find_one({'device_id': ObjectId(device_id)})

    def update_neighbor(self, device_id: str, device_ip: str, neighbor):
        try:
            device_id = ObjectId(device_id)
        except InvalidId:
            return None
        self.model.update_one({
            'device_id': device_id
        }, {
            '$set': {
                'device_id': device_id,
                # 'device_ip': device_ip,
                'neighbor': neighbor,
                'updated_at': sdn_utils.datetime_now()
            }
        }, upsert=True)
