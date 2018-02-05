import time
from pymongo import MongoClient
from config import Config
from flask import current_app

mongo = MongoClient('localhost', current_app.config['DB_PORT'])
db = mongo.sumica4

db.images.ensure_index('time')
db.hue.ensure_index('time')

def get_fb_id(username):
    result = db.fb_users.find_one({"username": username})
    if result:
        return result["fb_id"]

    return None

def log_command(command, controller):
    data = dict()
    data['time'] = time.time()
    data['command'] = command
    data['controller'] = controller.__class__.__name__
    db.commands.insert_one(data)
