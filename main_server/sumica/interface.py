import base64, os
import time

from flask import Blueprint, request, current_app, render_template, jsonify
import coloredlogs
import logging

from utils import db
import controllermanager as cm

logger = logging.getLogger(__name__)
coloredlogs.install(level=current_app.config['LOG_LEVEL'], logger=logger)

bp = Blueprint("interface", __name__)


@bp.route('/interface', methods=['GET'])
def interface():
    username = request.args.get('username')

    return render_template('interface.html')

@bp.route('/feed', methods=['POST'])
def feed():
    images = []
    #username = request.args.get('username')
    max_lag = 10
    start_time = time.time() - max_lag
    end_time = time.time()
    query = {"user_name": "sean", "time": {"$gt": start_time, "$lt": end_time}}
    results = db.images.find(query)
    cams = results.distinct("cam_id")
    cams.sort()

    for cam in cams:
        query = {"user_name": "sean", "time": {"$gt": start_time, "$lt": end_time}, "cam_id": cam}
        result = db.images.find(query).limit(1).sort([("time", -1)])[0]

        with open(current_app.config["RAW_IMG_DIR"] + result["filename"], "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
            encoded_string = encoded_string.decode("utf-8")
            images.append({"name": cam, "img": encoded_string})

    data = jsonify(images)

    return data