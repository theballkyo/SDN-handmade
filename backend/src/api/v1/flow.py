from bson.json_util import dumps
from sanic.response import json
from sanic.views import HTTPMethodView


class FlowView(HTTPMethodView):

    def get(self, request):
        flows = request.app.db['flow_stat'].get_all().sort("in_bytes", -1)
        return json({"flows": flows, "status": "ok"}, dumps=dumps)
