from flask import Blueprint, request, jsonify
import database as db
import coloredlogs, logging
import time

bp = Blueprint("speech", __name__)
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', logger=logger)

@bp.route('/data/speech', methods=['POST'])
def post_speech_data():
    data = request.form.to_dict()
    logger.debug(str(data))
    data["time"] = float(data["time"])

    db.mongo.speech.insert_one(data)

    db.trigger_controllers(data['user_name'], "speech", data)

    data.pop("_id")
    return jsonify(data), 201


@bp.route('/data/confirmation', methods=['POST'])
def post_confirm_data():
    data = request.form.to_dict()
    logger.debug(str(data))
    data["time"] = time.time()
    db.mongo.confirmation.insert_one(data)
    db.trigger_controllers(data['user_name'], "confirmation", data)
    data.pop("_id")
    return jsonify(data), 201


