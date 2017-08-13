from pymongo import MongoClient
client = MongoClient()
mongo = client.hai

from controllers.controller import Sample
from controllers.detection import Detection
from controllers.chatbot import Chatbot
from controllers.hello import HelloController

def standard_controllers(user_name):
    return [Sample(), Detection(), Chatbot(), HelloController(user_name)]

# TODO: use DB
controllers_objects = {}
controllers_objects['koki'] = standard_controllers('koki')
controllers_objects['sean'] = standard_controllers('sean')
