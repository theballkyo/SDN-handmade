from repository.repository import Repository


class UsedFlowIdRepository(Repository):
    def __init__(self):
        super(UsedFlowIdRepository, self).__init__()
        self.seq = self.db.used_flow_id
        self.model = self.db.used_flow_id

    def get_new_id(self):
        seq = self.seq.find_one({'in_use': False}, {'_id': 1})
        if seq:
            return seq['_id']
        return None

    def set_use_id(self, _id):
        self.seq.update_one({'_id': _id}, {'$set': {'in_use': True}})

    def set_not_use_id(self, _id):
        self.seq.update_one({'_id': _id}, {'$set': {'in_use': False}})
