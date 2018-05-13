from ipaddress import IPv4Address, AddressValueError

from bson.json_util import dumps
from sanic.response import json
from sanic.views import HTTPMethodView

from repository import DeviceRepository


class DeviceView(HTTPMethodView):

    def get(self, request, device_id=None):
        device_repo = request.app.db['device']

        if device_id is None:
            devices = device_repo.get_all()
            return json({"devices": devices, "success": True}, dumps=dumps)

        try:
            ip_address = IPv4Address(device_id)
            ip_address = str(ip_address)
            device = device_repo.find_by_if_ip(ip_address,
                                               project=device_repo.project_simple()
                                               )
        except AddressValueError:
            device = request.app.db['device'].get_by_id(device_id)

        return json({"device": device, "success": True}, dumps=dumps)

    def post(self, request):
        device_repo = request.app.db['device']
        try:
            device = {
                'management_ip': request.json['management_ip'],
                'device_ip': request.json['management_ip'],
                'type': request.json['type'],
                'ssh_info': {
                    'username': request.json['ssh_info']['username'],
                    'password': request.json['ssh_info']['password'],
                    'port': request.json['ssh_info']['port'],
                    'secret': request.json['ssh_info']['secret']
                },
                'snmp_info': {
                    'version': request.json['snmp_info']['version'],
                    'community': request.json['snmp_info']['community'],
                    'port': request.json['snmp_info']['port']
                },
                'status': DeviceRepository.STATUS_ACTIVE
            }
        except ValueError:
            return json({'success': False, 'message': 'Invalidate form'})

        device_repo.add_device(device)
        return json({'success': True, 'message': request.json})

    def patch(self, request, device_id):
        request.app.db["device"].set_information(device_id, request.json)
        return json({"status": True, "message": "Update device!"})

    def delete(self, request):
        device_id = request.args.get('device_id')
        if not device_id:
            return json({'status': False, 'message': 'Flow id not exist'})

        request.app.db['device'].set_status_wait_remove(device_id)
        return json({'status': True, 'message': 'Removed device'}, status=200)


class DeviceNeighborView(HTTPMethodView):

    def get(self, request, device_id):
        device_neighbor_repo = request.app.db['device_neighbor']
        try:
            ip = IPv4Address(device_id)
            ip = str(ip)
        except AddressValueError:
            device = request.app.db['device'].get_by_id(device_id)
            ip = device['management_ip']

        neighbor = device_neighbor_repo.get_by_management_ip(ip)
        return json({'neighbor': neighbor['neighbor'], 'success': True}, dumps=dumps)
