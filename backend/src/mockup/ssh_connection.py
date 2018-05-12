class FakeSSHConnection:

    def check_connection(self, d):
        return [True]

    def send_config_set(self, d):
        return True
