from netmiko import ConnectHandler


class Controller:
    pass

class SSHController:
    def __init__(self, ip, port, username, password,
                 secret, device_type, verbose=False):
        data = {
            'device_type': device_type,
            'ip':   ip,
            'username': username,
            'password': password,
            'port' : port,          # optional, defaults to 22
            'secret': secret,     # optional, defaults to ''
            'verbose': verbose,       # optional, defaults to False
        }
        self.net_connect = ConnectHandler(data)
        
    def send_command(self, command):
        return self.net_connect.send_command(command)
