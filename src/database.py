from pymongo import MongoClient
from config import MONGO_DB
class MongoDB:

    def __init__(self):
        self.client = MongoClient(MONGO_DB.get('host'))

        # Defind Database
        self.db = self.client.sdn_test

        # Defind Collection
        self.netflow = self.db.netflow

        self.snmp = self.db.snmp

        self.device = self.db.device

class NetflowDB(MongoDB):

    # def __init__(self, netflow):
    #     self.netflow = netflow

    def insert(self, data):
        self.netflow.insert_one(data)
