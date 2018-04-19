import router_command.cisco_ios_command as cisco_ios_cmd


def generate_config_command(flow):
    pass


def generate_remove_command(device_type, policy):
    if device_type == 'cisco_ios':
        return cisco_ios_cmd.generate_remove_command(policy)


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
