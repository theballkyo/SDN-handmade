from netmiko import ConnectHandler

cisco_881 = {
    'device_type': 'cisco_ios',
    'ip':   '192.168.122.2',
    'username': 'cisco',
    'password': 'cisco',
    # 'port' : 8022,          # optional, defaults to 22
    'secret': 'cisco',     # optional, defaults to ''
    'verbose': True,       # optional, defaults to False
}

net_connect = ConnectHandler(**cisco_881)
print("Conneced !")
net_connect.enable()
output = net_connect.send_command("show ip cache flow")
print(output)