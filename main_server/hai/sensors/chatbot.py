from flask import Blueprint, request
from server_actors import chatbot
import json

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

    import hai
    
    if fb_id != bot_id:
        hai.trigger_controllers(None, "user chat", event)
    #else:
    #    hai.trigger_controllers(data['user_id'], "unknown chat", event)

    return "ok", 201
