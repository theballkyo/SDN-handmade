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
}

net_connect = ConnectHandler(**cisco_881)
print("Connected !")
net_connect.enable()
# print("Starting...")
# s = time.time()
# out = net_connect.send_command("show run")
# print(out)
# print("Usage time: {:.2f}".format(time.time() - s))
# print("=" * 100)
# time.sleep(5)
# print("Starting...")
# s = time.time()
# out = net_connect.send_command_expect("show run")
# print(out)
# print("Usage time: {:.2f}".format(time.time() - s))
# print("=" * 100)
config = [
    'int lo0',
    'ip add 10.99.99.1 255.255.255.252',
    'assaas',
    'int lo1',
    'ip add 10.99.99.5 255.255.255.252'
]
time.sleep(5)
print("Starting...")
s = time.time()
out = net_connect.send_config_set(config)
print(out)
print("Usage time: {:.2f}".format(time.time() - s))

print("=" * 100)
time.sleep(5)
print("Starting...")
config_str = "\n".join(config)
s = time.time()
out = net_connect.send_config_set([config_str])
print(out)
print("Usage time: {:.2f}".format(time.time() - s))

# print(net_connect.read_channel())
# time.sleep(1)
# net_connect.write_channel('cisco\n')
# net_connect.write_channel('cisco\n')
# time.sleep(1)
# # print(net_connect.read_channel())
# net_connect.write_channel('enable\n')
# time.sleep(0.5)
# net_connect.write_channel('cisco\n')
# time.sleep(0.5)
# # net_connect.write_channel()
# print(net_connect.read_channel())
# net_connect.write_channel("terminal length 0\n")
# # net_connect.enable()
# output = net_connect.write_channel("show run\n")
# _buffer = ""
# for _ in range(20):
#     data = net_connect.read_channel()
#     _buffer += data
#     print(data)
#     time.sleep(0.1)
#     print("=" * 100)
# # output = net_connect.send_command("show run | section inteface")
# # print(output)
