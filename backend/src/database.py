""" Database management """
import pymongo
# from config.database import MONGO_DB
import os
import settings

DEFAULT_CONNECTION_NAME = None


def set_connection_name(name):
    global DEFAULT_CONNECTION_NAME
    DEFAULT_CONNECTION_NAME = name


_connections = {}


def get_mongodb(alias=None):
    # global _connections
    if not alias:
        alias = DEFAULT_CONNECTION_NAME
    alias_original = alias
    alias = alias + str(os.getpid())
    if _connections.get(alias) is None:
        # Check mongodb configuration
        config = settings.database.get(alias_original)
        if config is not None:
            if config.get('driver', '') != 'mongodb':
                raise ValueError("config driver is not mongodb")
            max_pool_size = config.get('max_pool_size', 10)
            _connections[alias] = MongoDB(config['uri'], config['database'], max_pool_size)
        else:
            raise ValueError("Can't find config alias name %s" % alias)
    return _connections[alias]
    # if alias not in _connections:
    #     # Check mongodb configuration
    #     config = settings.database.get(alias_original)
    #     if config is not None:
    #         if config.get('driver', '') != 'mongodb':
    #             raise ValueError("config driver is not mongodb")
    #         max_pool_size = config.get('max_pool_size', 10)
    #         _connections[alias] = MongoDB(config['uri'], config['database'], max_pool_size)
    #     else:
    #         raise ValueError("Can't find config alias name %s" % alias)
    # return _connections[alias]


def disconnect(alias=DEFAULT_CONNECTION_NAME):
    if alias in _connections:
        _connections[alias].client.close()
        del _connections[alias]


class MongoDB:
    def __init__(self, uri, database, max_pool_size=10):
        self.client = pymongo.MongoClient(uri, maxPoolSize=max_pool_size)
        self.pymongo = pymongo
        # Define Database
        self.db = self.client[database]

        # Define Collection
        self.netflow = self.db.netflow
        self.snmp = self.db.snmp
        self.device = self.db.device
        self.route = self.db.route

        self.flow_table = self.db.flow_table

        self.device_config = self.db.device_config
        self.cdp = self.db.cdp

        # Flow sequence
        self.flow_seq = self.db.flow_seq

        self.app = self.db.app
