from service.base_service import BaseService


class AppService(BaseService):
    def __init__(self):
        super(AppService, self).__init__()

    def is_running(self):
        app = self.db.app.find_one({}, {'is_running': 1})
        return app

    def set_running(self, running):
        self.db.app.update_one({}, {
            '$set': {
                'is_running': running
            }
        })
