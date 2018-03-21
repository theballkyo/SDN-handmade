from service import BaseService


class CdpService(BaseService):
    def __init__(self):
        super(CdpService, self).__init__()
        self.cdp = self.db.cdp

    def get_by_management_ip(self, management_ip):
        return self.db.cdp.find_one({'management_ip': management_ip})
