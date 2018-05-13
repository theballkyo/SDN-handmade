from abc import ABCMeta
from database import get_mongodb
from bson.objectid import ObjectId, InvalidId


class Repository(metaclass=ABCMeta):
    model = None

    def __init__(self):
        self.mongodb = get_mongodb()
        self.db = self.mongodb.db

    def find_by_id(self, _id: str, projection=None, **kwargs):
        try:
            object_id = ObjectId(_id)
        except (InvalidId, TypeError):
            return None

        return self.model.find_one({
            "_id": object_id
        }, projection, **kwargs)

    def delete_many(self, **kwargs):
        return self.model.delete_many(**kwargs)
