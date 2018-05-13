from bson.json_util import dumps
from sanic.response import json
from sanic.views import HTTPMethodView


class LinkView(HTTPMethodView):

    def get(self, request, _id=None):
        if _id:
            link = request.app.db['link_utilization'].find_by_id(_id)
            return json({"link": link, "status": "ok"}, dumps=dumps)

        links = request.app.db['link_utilization'].get_all()
        return json({"links": links, "status": "ok"}, dumps=dumps)
