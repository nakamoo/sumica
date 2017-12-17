import time
from flask import Flask
import pymongo

from server_actors import actor

app = Flask(__name__)
app.config.from_pyfile(filename="../application.cfg")
mongo = pymongo.MongoClient('localhost', app.config['PORT_DB']).hai


class Controller(object):
    def __init__(self, user):
        self.user = user

    def on_event(self, event, data):
        pass

    def execute(self):
        pass

    def log_operation(self, re):
        inserted_data = dict()
        inserted_data['operation'] = re
        inserted_data['time'] = time.time()
        inserted_data['user'] = self.user
        inserted_data['controller'] = self.__class__.__name__
        mongo.operation.insert_one(inserted_data)


class Sample(Controller):
    def __init__(self, gpu=-1):
        self.gpu = gpu

    def execute(self):
        # colect data from DB or api

        # logic

        actor.sample()

        response = []
        response.append({"app": "TV", "cmd": "turn on", "controller": "Sample"})
        response.append({"app": "music", "cmd": "pray", "controller": "Sample"})
        return response

