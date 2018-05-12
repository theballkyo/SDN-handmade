from sanic.views import HTTPMethodView
from sanic.response import text, json
from bson.json_util import dumps


class LinkView(HTTPMethodView):

    def get(self, request, id=None):
        if id:
            link = request.app.db['link'].find_by_id(id)
            return json({"link": link, "status": "ok"}, dumps=dumps)

        links = request.app.db['link'].get_all()
        return json({"links": links, "status": "ok"}, dumps=dumps)
