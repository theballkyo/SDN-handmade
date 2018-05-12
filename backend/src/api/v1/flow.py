from sanic.views import HTTPMethodView
from sanic.response import text, json
from bson.json_util import dumps


class FlowView(HTTPMethodView):

    def get(self, request, id=None):
        # if id:
        flows = request.app.db['netflow'].get_all()
        return json({"flows": flows, "status": "ok"}, dumps=dumps)
        #
        # links = request.app.db['link'].get_all()
        # return json({"links": links, "status": "ok"}, dumps=dumps)
