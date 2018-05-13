import multiprocessing as mp

from sanic import Sanic
from sanic.response import json
from sanic.views import HTTPMethodView
from sanic_cors import CORS

import settings
from repository import get_all
from .v1 import api_v1


class SimpleView(HTTPMethodView):

    def get(self, request):
        return json({"success": True, "message": "Test"})


class RestServer:
    app_ = Sanic(__name__)

    def __init__(self):
        self.server = None

    def run(self):
        self.server = mp.Process(target=self._run)
        # self.server.daemon = True
        self.server.start()
        try:
            self.server.join()
        except KeyboardInterrupt:
            self.shutdown()

    @staticmethod
    @app_.listener('before_server_start')
    async def setup_db(app, loop):
        app.db = get_all()

    def _run(self):
        CORS(self.app_, automatic_options=True)
        self.app_.add_route(SimpleView.as_view(), '/')
        # self.app_.add_route(DeviceView.as_view(), '/device')
        self.app_.blueprint(api_v1, url_prefix='/api/v1')
        self.app_.run(host=settings.rest_api['host'], port=5001)

    def shutdown(self):
        if self.server:
            self.server.terminate()
            self.server.join()
