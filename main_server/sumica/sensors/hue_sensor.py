import json

from flask import Blueprint, request, jsonify, current_app
import coloredlogs
import logging

import controllermanager as cm
from utils import db

logger = logging.getLogger(__name__)
coloredlogs.install(level=current_app.config['LOG_LEVEL'], logger=logger)

bp = Blueprint("hue", __name__)


@bp.route('/data/hue', methods=['POST'])
def post_hue_data():
    data = request.form.to_dict()

    data["time"] = float(data["time"])
    data['light_states'] = json.loads(data['lights'])

    db.hue.insert_one(data)

    cm.trigger_controllers(data['user_name'], "hue", data)

    data.pop("_id")
    
    return jsonify(data), 201
