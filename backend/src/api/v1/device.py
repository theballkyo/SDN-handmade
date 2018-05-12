from sanic.views import HTTPMethodView
from sanic.response import text, json
from bson.json_util import dumps
from ipaddress import IPv4Address, AddressValueError


class DeviceView(HTTPMethodView):

    def get(self, request, id=None, ip=None):
        if ip:
            device_repo = request.app.db['device']
            device = device_repo.find_by_if_ip(ip, project=device_repo.project_simple())
            return json({'device': device}, dumps=dumps)
        if id:
            device = request.app.db['device'].get_by_id(id)
            return json({'device': device}, dumps=dumps)
        devices = request.app.db['device'].get_all()
        return json({"devices": devices, "status": "ok"}, dumps=dumps)

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
                    'community': request.json['snmp_info']['community'],
                    'port': request.json['snmp_info']['port']
                }
            }
        except ValueError:
            return json({'success': False, 'message': 'Invalidate form'})

        device_repo.add_device(device)
        return json({'success': True, 'message': request.json})

    def delete(self, request):
        pass


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
