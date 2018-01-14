import time
import json

from flask import Blueprint, request, jsonify
import coloredlogs
import logging

import controllermanager as cm
from utils import db

bp = Blueprint("speech", __name__)
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', logger=logger)


@bp.route('/data/speech', methods=['POST'])
def post_speech_data():
    data = request.form.to_dict()

    data["time"] = float(data["time"])

    db.speech.insert_one(data)

    cm.trigger_controllers(data['user_name'], "speech", data)

    data.pop("_id")

    return jsonify(data), 201


@bp.route('/data/confirmation', methods=['POST'])
def post_confirm_data():
    data = request.form.to_dict()
    logger.debug(str(data))
    data["time"] = time.time()
    data["action"] = json.loads(data["action"])
    db.confirmation.insert_one(data)
    cm.trigger_controllers(data['user_name'], "confirmation", data)
    data.pop("_id")
    return jsonify(data), 201


