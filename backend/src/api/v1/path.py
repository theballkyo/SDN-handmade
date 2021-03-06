from bson.json_util import dumps
from sanic.response import json
from sanic.views import HTTPMethodView

from tools import PathFinder


class PathView(HTTPMethodView):

    def get(self, request, src_dst):
        src, dst = src_dst.split(',')
        path_finder = PathFinder()
        paths = path_finder.all_by_manage_ip(src, dst)
        paths = set(map(tuple, paths))
        return json({"paths": paths, "status": "ok"}, dumps=dumps)
