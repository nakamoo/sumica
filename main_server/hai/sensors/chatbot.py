from flask import Blueprint, request
from server_actors import chatbot
import json
import database as db

app = Blueprint("chatbot", __name__)

# temporary
fb2user = {}

bot_id = "318910425200757"

# messenger
@app.route('/data/fb', methods=['POST'])
def post_fb_data():
    data = request.form.to_dict()
    event = json.loads(data["event"])
    fb_id = event["sender"]["id"]
    print(data)
    username = None

    n = db.mongo.fb_users.find_one({"fb_id": fb_id})
    if n:
        username = n["id"]
    
    if fb_id != bot_id:
        db.trigger_controllers(username, "chat", event)

    return "ok", 201
