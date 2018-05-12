from sanic import Sanic
from sanic.views import HTTPMethodView
from sanic.response import text, json
import multiprocessing as mp
import settings
from repository import get_all_service
from bson.json_util import dumps, RELAXED_JSON_OPTIONS
from sanic_cors import CORS, cross_origin
import pprint
from .v1 import api_v1


class SimpleView(HTTPMethodView):

    def __init__(self):
        self.link_service = get_service('link')

    def get(self, request):
        # link_service = get_service('link')
        links = request.app.db['link'].get_all()
        return json(
            {"links": links, "status": "ok"}, dumps=dumps)


class DeviceView(HTTPMethodView):

    def get(self, request):
        pass


class RestServer:
    app_ = Sanic(__name__)

    def __init__(self):
        self.server = None

    def run(self):
        self.server = mp.Process(target=self._run, daemon=False).start()

    @app_.listener('before_server_start')
    async def setup_db(app, loop):
        # app.db = {}
        # app.db['link'] = get_service('link')
        app.db = get_all_service()

    def _run(self):
        CORS(self.app_, automatic_options=True)
        self.app_.add_route(SimpleView.as_view(), '/')
        self.app_.add_route(DeviceView.as_view(), '/device')
        self.app_.blueprint(api_v1, url_prefix='/api/v1')
        self.app_.run(host=settings.rest_api['host'], port=5001)

    def shutdown(self):
        if self.server:
            self.server.terminate()
            self.server.join()
