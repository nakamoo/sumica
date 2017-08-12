from flask import Blueprint
from ..sensors import chatbot

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

    if fb_id != bot_id:
        hai.trigger_controllers(data['user_id'], "user chat", event)
    #else:
    #    hai.trigger_controllers(data['user_id'], "unknown chat", event)

    return "ok", 201