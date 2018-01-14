from pymongo import MongoClient
from config import Config
from flask import current_app

mongo = MongoClient('localhost', current_app.config['DB_PORT'])
db = mongo.sumica

db.images.ensure_index('time')
db.hue.ensure_index('time')

def get_fb_id(username):
    result = db.fb_users.find_one({"username": username})
    if result:
        return result["fb_id"]

    return None