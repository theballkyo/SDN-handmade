from bson.json_util import dumps
from sanic.response import json
from sanic.views import HTTPMethodView

from repository import PolicyRoute


class FlowRoutingView(HTTPMethodView):

    def get(self, request, id=None):
        if id:
            flow = request.app.db['flow_routing'].get_by_id(id)
            return json({'flow': flow, 'status': 'ok'}, dumps=dumps)
        flows = request.app.db['flow_routing'].get_all()
        return json({"flows": flows, "status": "ok"}, dumps=dumps)

    def post(self, request):
        try:
            actions = []
            for action in request.json['actions']:
                actions.append({
                    'device_id': action['device_id'],
                    # 'management_ip': action['management_ip'],
                    'action': int(action['action']),
                    'data': action['data']
                })

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
            return json({'success': False, 'message': 'Invalid form'})

        policy_repo = request.app.db['flow_routing']
        policy_repo.add_or_update_flow_routing(policy)
        return json({'status': 'ok'}, status=201)

    def patch(self, request):
        try:
            actions = []
            for action in request.json['actions']:
                actions.append({
                    'device_id': action['device_id'],
                    # 'management_ip': action['management_ip'],
                    'action': int(action['action']),
                    'data': action['data']
                })

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

        request.app.db['flow_routing'].add_or_update_flow_routing(flow)
        return json({'success': True})

    def delete(self, request):
        flow_id = request.args.get('flow_id')
        if not flow_id or not flow_id.isdigit():
            return json({'status': False, 'message': 'Flow id not exist'})

        flow_id = int(flow_id)
        request.app.db['flow_routing'].set_status_wait_remove(flow_id)
        return json({'status': True, 'message': 'Removed flow routing'}, status=204)
