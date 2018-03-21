from flask import Flask, request
import multiprocessing as mp
import settings


class RestServer:
    app = Flask(__name__)

    def __init__(self):
        self.server = None

    @app.route("/")
    def hello():
        return "Hello World!"

    def run(self):
        self.server = mp.Process(target=self._run, daemon=True).start()

    def _run(self):
        self.app.run(host=settings.rest_api['host'], port=settings.rest_api['port'])

    def shutdown(self):
        if self.server:
            self.server.terminate()
            self.server.join()
