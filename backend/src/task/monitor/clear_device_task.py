import logging
import pprint

from repository import get_service
from router_command.policy_command import generate_remove_command
from worker.ssh.ssh_worker import SSHConnection


class ClearDeviceTask:

    def __init__(self):
        self.device_repo = get_service("device")
        self.flow_routing_repo = get_service("policy")
        self.flow_routing_seq_repo = get_service("policy_seq")
        self.device_neighbor_repo = get_service("cdp")
        self.link_repo = get_service("link")
        self.routing_repo = get_service("route")
        self.flow_stat_repo = get_service("netflow")

    def get_devices(self):
        return self.device_repo.device.find({
            "status": -1,
        })

    def get_flow_routing(self, device_ip):
        return self.flow_routing_repo.policy.find({
            "actions.management_ip": device_ip
        })

    def remove_neighbor(self, device_ip):
        logging.info("Removed neighbor")
        self.device_neighbor_repo.cdp.remove({
            "management_ip": device_ip
        })

    def remove_link(self, device_ip):
        logging.info("Removed link")
        self.link_repo.link.remove({
            "$or": [
                {
                    "src_node_ip": device_ip
                },
                {
                    "dst_node_ip": device_ip
                }
            ]
        })

    def remove_route(self, device_ip):
        logging.info('Removed Route')
        self.routing_repo.route.remove({
            "device_ip": device_ip
        })

    def remove_flow_stat(self, device_ip):
        logging.info("Removed flow stat")
        self.flow_stat_repo.model.remove({
            "from_ip": device_ip
        })

    def remove_flow_routing(self, flow_id):
        self.flow_routing_repo.model.remove({
            "flow_id": flow_id
        })

    def remove_device(self, device_ip):
        self.device_repo.device.remove({
            "management_ip": device_ip
        })

    def remove_process(self, device, ssh_connection: SSHConnection):
        logging.info(pprint.pformat(device))
        device_ip = device['management_ip']

        # Remove Flow routing !
        # Find flow is passing the device
        # Action ...
        flows_routing = self.get_flow_routing(device['management_ip'])
        logging.info("Removed Flow routing")

        device_list = {}
        # Remove old action
        for flow in flows_routing:
            for action in flow['actions']:
                if device_list.get(action['management_ip']):
                    continue

                logging.info(pprint.pformat("Node ID: {}".format(action['management_ip'])))
                device = self.device_repo.get_device(action['management_ip'])
                cmd = generate_remove_command(device['type'], flow)
                device_list[action['management_ip']] = cmd

            # Send SSH Command
            connect = ssh_connection.check_connection(device_list.keys())
            # pprint.pprint(connect)
            if not all(connect):
                logging.info("Some device can't SSH")
                return
            logging.info("Update...")
            ssh_connection.send_config_set(device_list)
            logging.info(pprint.pformat(device_list))
            self.flow_routing_seq_repo.set_not_use_id(flow['flow_id'])

            # Remove flow routing
            self.remove_flow_routing(flow['flow_id'])

        # Remove Neighbor
        self.remove_neighbor(device_ip)

        # Remove Link
        self.remove_link(device_ip)

        # Remove Route
        self.remove_route(device_ip)

        # Remove Flow stat
        self.remove_flow_stat(device_ip)

        # Remove Device
        self.remove_device(device_ip)
        logging.info("END")

    def run(self, ssh_connection: SSHConnection):
        # Find device status is waiting for remove
        devices = self.get_devices()
        for device in devices:
            self.remove_process(device, ssh_connection)
