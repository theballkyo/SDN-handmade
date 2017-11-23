""" Database management """
import pymongo
from config import MONGO_DB
import os

DEFAULT_CONNECTION_NAME = 'default'

_connections = {}


def get_connection(alias=DEFAULT_CONNECTION_NAME):
    # Todo
    alias = alias + str(os.getpid())
    if alias not in _connections:
        _connections[alias] = MongoDB()

    return _connections[alias]


def disconnect(alias=DEFAULT_CONNECTION_NAME):
    alias = alias + str(os.getpid())
    if alias in _connections:
        _connections[alias].client.close()
        del _connections[alias]

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
        self.cdp = self.db.cdp

        # Flow sequence
        self.flow_seq = self.db.flow_seq


# class NetflowDB(MongoDB):
#
#     # def __init__(self, netflow):
#     #     self.netflow = netflow
#
#     def insert(self, data):
#         self.netflow.insert_one(data)
