import router_command.cisco_ios_command as cisco_ios_cmd
import router_command.cisco_ios_v15_command as cisco_ios_15_cmd


def generate_config_command(device_type, flow, flow_id, flow_name, action):
    if device_type == 'cisco_ios':
        return cisco_ios_cmd.generate_cmd(flow, flow_id, flow_name, action)
    elif device_type == 'cisco_ios_v15':
        return cisco_ios_15_cmd.generate_cmd(flow, flow_id, flow_name, action)


def generate_remove_command(device_type, flow):
    if device_type == 'cisco_ios':
        return cisco_ios_cmd.generate_remove_command(flow)
    elif device_type == 'cisco_ios_v15':
        return cisco_ios_15_cmd.generate_remove_command(flow)


def get_netmiko_type(device_type):
    if device_type == 'cisco_ios':
        return cisco_ios_cmd.get_netmiko_type()
    elif device_type == 'cisco_ios_v15':
        return cisco_ios_15_cmd.get_netmiko_type()


def generate_policy_command(device_type, policy):
    if device_type == 'cisco_ios':
        # cmd = CiscoIosFlowCommand(flow)
        return cisco_ios_cmd.generate_policy_command(policy)
    else:
        raise ValueError("No device type: {}".format(device_type))


def generate_action_command(device_type, flow_id, flow_name, action):
    if device_type == 'cisco_ios':
        # cmd = CiscoIosFlowCommand(flow)
        return cisco_ios_cmd.generate_action_command(flow_id, flow_name, action)
    else:
        raise ValueError("No device type: {}".format(device_type))
