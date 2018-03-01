from database import get_mongodb


class BaseService:
    def __init__(self):
        self.mongodb = get_mongodb()
        self.db = self.mongodb.db
