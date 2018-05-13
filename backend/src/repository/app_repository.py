from repository.repository import Repository


class AppRepository(Repository):
    def __init__(self):
        super(AppRepository, self).__init__()
        self.model = self.db.app

    def is_running(self):
        return self.model.find_one({}, {'is_running': 1})

    def set_running(self, running):
        self.model.update_one({}, {
            '$set': {
                'is_running': running
            }
        })
