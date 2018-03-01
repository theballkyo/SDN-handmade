from service import BaseService


class PolicySeqService(BaseService):
    def __init__(self):
        super(PolicySeqService, self).__init__()
        self.seq = self.db.flow_seq

    def get_new_id(self):
        seq = self.seq.find_one({'in_use': False}, {'_id': 1})
        if seq:
            return seq['_id']
        return None
