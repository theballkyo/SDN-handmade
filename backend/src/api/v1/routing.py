from bson.json_util import dumps
from sanic.response import json
from sanic.views import HTTPMethodView


class RoutingView(HTTPMethodView):

    def get(self, request, device_id):
        cr_repo = request.app.db['copied_route']
        routes = cr_repo.get_by_device_id(device_id)
        # flows = request.app.db['flow_stat'].get_all().sort("in_bytes", -1)
        return json({"routes": routes, "status": "ok"}, dumps=dumps)
