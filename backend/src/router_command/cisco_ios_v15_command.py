def generate_cmd(flow, flow_id, flow_name, action):
    return ["ip access-list extends id-" + flow_id,
            "route-map test001"]


def generate_remove_command(flow):
    return ["no ip access-list extends id-" + flow['flow_id']]


def get_netmiko_type():
    return "cisco_ios"
