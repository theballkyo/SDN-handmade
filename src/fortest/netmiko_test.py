from netmiko import ConnectHandler

cisco_881 = {
    'device_type': 'generic_termserver',
    'ip':   '192.168.122.2',
    'username': 'cisco',
    'password': 'cisco',
    # 'port' : 8022,          # optional, defaults to 22
    'secret': 'cisco',     # optional, defaults to ''
    'verbose': True,       # optional, defaults to False
}

net_connect = ConnectHandler(**cisco_881)
print("Conneced !")
net_connect.write_channel('enable\ncisco\n')
print(net_connect.read_channel())
# net_connect.enable()
output = net_connect.send_command("show run | section ip access-list")
print(output)