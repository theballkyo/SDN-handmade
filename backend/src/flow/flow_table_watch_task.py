import logging
from repository import get_flow_table_service
from flow import FlowState
from services import get_service
from router_command import generate_action_command, generate_policy_command


class FlowTableWatchTask:
    def __init__(self):
        self.fts = get_flow_table_service()
        self.device_service = get_service('device')

    def run_task(self, ssh_connection, flow):
        ips = []
        cmd_list = {}

        actions = flow.get('action_pending')
        if not actions:
            return True

        for action in actions:
            worker_queue = ssh_connection.get(action['device_ip'])
            if not worker_queue:
                return False
            worker_queue['work_q'].put({'type': 'recheck'})
            ips.append(action['device_ip'])

            device_ip = action["device_ip"]
            ssh_info = self.device_service.get_ssh_info(device_ip)
            if not ssh_info:
                continue

            flow_cmd = generate_policy_command(ssh_info['device_type'], flow)
            action_cmd = generate_action_command(ssh_info['device_type'], flow, action)
            cmd = flow_cmd + action_cmd
            cmd_list[action['device_ip']] = cmd

        already = []
        for ip in ips:
            already.append(ssh_connection[ip]['result_q'].get())

        if not all(already):
            return False

        for ip, cmd in cmd_list.items():
            ssh_connection[ip]['work_q'].put({'type': 'send_config', 'data': cmd})

        results = []
        for ip in ips:
            results.append(ssh_connection[ip]['result_q'].get())

        if not all(already):
            return False
        else:
            return True

    def run(self, ssh_connection):
        logging.info("Flow watching is running...")
        # Limit by one flow
        flows = self.fts.get_flows_by_state(FlowState.WAIT_FOR_PROCESS, 1)

        # Not have flow is waiting for process
        if flows.count() == 0:
            return True

        flow = flows[0]
        self.fts.set_flow_state(flow['flow_id'], FlowState.PROCESSING)
        ok = self.run_task(ssh_connection, flow)
        if ok:
            self.fts.set_flow_state(flow['flow_id'], FlowState.IDLE)
        else:
            self.fts.set_flow_state(flow['flow_id'], FlowState.WAIT_FOR_PROCESS)
