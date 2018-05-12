import netaddr
from sanic.views import HTTPMethodView
from sanic.response import text, json
from bson.json_util import dumps

from repository import PolicyRoute


class FlowRoutingView(HTTPMethodView):

    def get(self, request, id=None):
        if id:
            flow = request.app.db['policy'].get_by_id(id)
            return json({'flow': flow, 'status': 'ok'}, dumps=dumps)
        flows = request.app.db['policy'].get_all()
        return json({"flows": flows, "status": "ok"}, dumps=dumps)

    def post(self, request):
        try:
            actions = {}
            for action in request.json['actions']:
                a_key = action['device_id']
                actions[a_key] = {
                    'device_id': action['device_id'],
                    # 'management_ip': action['management_ip'],
                    'action': int(action['action']),
                    'data': action['data']
                }

            policy = {
                # 'policy_id': policy_id,
                'new_flow': {
                    'name': request.json['name'],
                    'src_ip': request.json['src_ip'],
                    'src_port': request.json['src_port'],
                    'src_wildcard': request.json['src_subnet'],
                    'dst_ip': request.json['dst_ip'],
                    'dst_port': request.json['dst_port'],
                    'dst_wildcard': request.json['dst_subnet'],
                    'actions': actions,
                },
                'info': {
                    'submit_from': {
                        'type': PolicyRoute.TYPE_STATIC,
                        'user': 'Unknown - Todo Implement'
                    },
                    'status': PolicyRoute.STATUS_WAIT_APPLY
                }
            }
        except (KeyError, ValueError) as e:
            print(e)
            return json({'success': False, 'message': 'Invalidate form'})

        policy_repo = request.app.db['policy']
        policy_repo.add_or_update_flow_routing(policy)
        return json({'success': True}, status=201)

    def patch(self, request):
        try:
            actions = {}
            for action in request.json['actions']:
                a_key = str(netaddr.IPAddress(action['management_ip']).value)
                actions[a_key] = {
                    'management_ip': action['management_ip'],
                    'action': int(action['action']),
                    'data': action['data']
                }

            # Get policy ID
            # policy_id = request.app.db['policy_seq'].get_new_id()
            # if not policy_id:
            #     return json({'success': False, 'message': 'Maximum flow routing'})

            flow = {
                # 'policy_id': policy_id,
                'new_flow': {
                    'name': request.json['name'],
                    'src_ip': request.json['src_ip'],
                    'src_port': request.json['src_port'],
                    'src_wildcard': request.json['src_subnet'],
                    'dst_ip': request.json['dst_ip'],
                    'dst_port': request.json['dst_port'],
                    'dst_wildcard': request.json['dst_subnet'],
                    'actions': actions,
                },
                'info': {
                    'submit_from': {
                        'type': PolicyRoute.TYPE_STATIC,
                        'user': 'Unknown - Todo Implement'
                    },
                    'status': PolicyRoute.STATUS_WAIT_APPLY
                },
                'flow_id': request.json['flow_id']
            }
        except (KeyError, ValueError) as e:
            print(e)
            return json({'success': False, 'message': 'Invalidate form'})

        request.app.db['policy'].add_or_update_flow_routing(flow)
        return json({'success': True})

    def delete(self, request):
        flow_id = request.json.get('flow_id')
        if not flow_id:
            return json({'success': False, 'message': 'Flow id not exist'})

        request.app.db['policy'].set_status_wait_remove(flow_id)
        return json({'success': True, 'message': 'Removed flow routing'})
