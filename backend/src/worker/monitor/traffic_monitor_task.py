from services import get_service


class TrafficMonitorTask:
    def __init__(self):
        self.is_stop = False
        self.device_service = get_service('device')

    def stop(self):
        self.is_stop = True

    def run(self):
        while not self.is_stop:
            devices = self.device_service.get_all()
            for device in devices:
                pass
