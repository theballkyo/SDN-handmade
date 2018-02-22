import router_command.cisco_ios_command as cisco_ios_cmd


def generate_config_command(flow):
    pass


def generate_flow_command(device_type, flow):
    if device_type == 'cisco_ios':
        # cmd = CiscoIosFlowCommand(flow)
        return cisco_ios_cmd.generate_flow_command(flow)
    else:
        raise ValueError("No device type: {}".format(device_type))


def generate_action_command(device_type, flow, action):
    if device_type == 'cisco_ios':
        # cmd = CiscoIosFlowCommand(flow)
        return cisco_ios_cmd.generate_action_command(flow, action)
    else:
        raise ValueError("No device type: {}".format(device_type))
