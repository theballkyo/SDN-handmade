from netmiko import ConnectHandler
import time
import timeit

cisco_881 = {
    'device_type': 'cisco_ios',  # generic_termserver
    'ip': '192.168.1.1',
    'username': 'cisco',
    'password': 'cisco',
    # 'port' : 8022,          # optional, defaults to 22
    'secret': 'cisco',  # optional, defaults to ''
    'verbose': True,  # optional, defaults to False
    'global_delay_factor': 0.5
}

net_connect = ConnectHandler(**cisco_881)
print("Connected !")
net_connect.enable()
config = [
    'int lo0',
    'ip add 10.99.99.1 255.255.255.252',
    'assaas',
    'int lo1',
    'ip add 10.99.99.5 255.255.255.252',
    'int lo0',
    'ip add 10.99.99.1 255.255.255.252',
    'int lo1',
    'ip add 10.99.99.5 255.255.255.252',
    'int lo0',
    'ip add 10.99.99.1 255.255.255.252',
    'int lo1',
    'ip add 10.99.99.5 255.255.255.252'
]
time.sleep(1)
print(net_connect.is_alive())
# print("Starting...")
# s = time.time()
# out = net_connect.send_config_set(config)
# print(out)
# print("Usage time: {:.2f}".format(time.time() - s))

print("=" * 100)
time.sleep(1)
print("Starting...")
config_str = "\n".join(config)
s = time.time()
out = net_connect.send_config_set([config_str])
# print(out)
print("Usage time: {:.2f}".format(time.time() - s))
net_connect.exit_config_mode()

print("=" * 100)
time.sleep(1)
print("Starting...")
s = time.time()
out1 = net_connect.send_command('show run')
out2 = net_connect.send_command('show ip inter br')
out3 = net_connect.send_command('show ip route')
print("Usage time: {:.2f}".format(time.time() - s))
print(net_connect.is_alive())
# print(out1)
# print(out2)
# print(out3)
