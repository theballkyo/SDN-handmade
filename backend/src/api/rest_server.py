from flask import Flask
import multiprocessing as mp
import settings

class RestServer:
    app = Flask(__name__)

    def __init__(self):
        pass

    @app.route("/")
    def hello():
        return "Hello World!"

    def run(self):
        mp.Process(target=self.__run, daemon=True).start()
    
    def __run(self):
        self.app.run(host=settings.rest_api['host'], port=settings.rest_api['port'])
