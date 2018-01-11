import json
import time

from flask import Blueprint, request, current_app
import coloredlogs
import logging

from server_actors import chatbot_actor
import controllermanager as cm

logger = logging.getLogger(__name__)
coloredlogs.install(level=current_app.config['LOG_LEVEL'], logger=logger)

bp = Blueprint("chatbot", __name__)

bot_id = current_app.config['FB_BOT_ID']
VERIFY_TOKEN = 'my_voice_is_my_password_verify_me'


@bp.route('/data/fb', methods=['GET'])
def handle_verification():
    logger.debug("Handling Verification.")

    if request.args.get('hub.verify_token', '') == VERIFY_TOKEN:
        logger.debug("Verification successful!")
        return request.args.get('hub.challenge', '')
    else:
        logger.debug("Verification failed!")
        return 'Error, wrong validation token'


@bp.route('/data/fb', methods=['POST'])
def handle_messages():
    payload = request.get_json()

    for event in messaging_events(payload):
        fb_id = event["sender"]["id"]

        username = None

        result = db.mongo.fb_users.find_one({"fb_id": fb_id})
        if result:
            username = result["id"]
            
        logger.debug("new message: " + str(event))

        # ignore messages by self
        if fb_id != bot_id:
            em.trigger_controllers(username, "chat", event)

    return "ok", 200


def messaging_events(payload):
    # Generate tuples of (sender_id, message_text) from the
    # provided payload.

    events = payload["entry"][0]["messaging"]

    for event in events:
        if "message" in event:
            yield event
