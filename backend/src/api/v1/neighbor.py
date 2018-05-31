from bson.json_util import dumps
from sanic.response import json
from sanic.views import HTTPMethodView


class NeighborView(HTTPMethodView):

    def get(self, request, device_id):
        dn_repo = request.app.db['device_neighbor']
        neighbors = dn_repo.get_by_device_id(device_id)
        # flows = request.app.db['flow_stat'].get_all().sort("in_bytes", -1)
        return json({"neighbors": neighbors, "status": "ok"}, dumps=dumps)
