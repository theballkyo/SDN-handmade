""" Database management """
import pymongo
from config import MONGO_DB


class MongoDB:
    def __init__(self):
        self.client = pymongo.MongoClient(MONGO_DB.get('host'))
        self.pymongo = pymongo
        # Defind Database
        self.db = self.client.sdn_test2

        # Defind Collection
        self.netflow = self.db.netflow
        self.snmp = self.db.snmp
        self.device = self.db.device
        self.route = self.db.route

        self.flow_table = self.db.flow_table

        self.device_config = self.db.device_config

    def close(self):
        self.client.close()


class NetflowDB(MongoDB):

    # def __init__(self, netflow):
    #     self.netflow = netflow

    def insert(self, data):
        self.netflow.insert_one(data)
