from flask import Blueprint, request
from server_actors import chatbot
import json
import database as db

bp = Blueprint("chatbot", __name__)

# temporary
fb2user = {}

bot_id = "318910425200757"

# messenger
@bp.route('/data/fb', methods=['POST'])
def post_fb_data():
    data = request.form.to_dict()
    event = json.loads(data["event"])
    fb_id = event["sender"]["id"]
    
    username = None

    n = db.mongo.fb_users.find_one({"fb_id": fb_id})
    if n:
        username = n["id"]
    
    if fb_id != bot_id:
        db.trigger_controllers(username, "chat", event)

    return "ok", 201

"""
@bp.route('/data/fb/', methods=['GET'])
def handle_verification():
  print("Handling Verification.")
  if request.args.get('hub.verify_token', '') == 'my_voice_is_my_password_verify_me':
    print("Verification successful!")
    return request.args.get('hub.challenge', '')
  else:
    print("Verification failed!")
    return 'Error, wrong validation token'

@bp.route('/data/fb/', methods=['POST'])
def handle_messages():
  print("Handling Messages")
  payload = request.get_data()
  print(payload)
  for event in messaging_events(payload):
    fb_id = event["sender"]["id"]
    
    username = None

    n = db.mongo.fb_users.find_one({"fb_id": fb_id})
    if n:
        username = n["id"]
    
    if fb_id != bot_id:
        db.trigger_controllers(username, "chat", event)
        
  return "ok"

def messaging_events(payload):
  #Generate tuples of (sender_id, message_text) from the
  #provided payload.
  
  data = json.loads(payload)
  messaging_events = data["entry"][0]["messaging"]
  for event in messaging_events:
    yield event
"""