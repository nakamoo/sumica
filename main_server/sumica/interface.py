import base64, os
import time

from flask import Blueprint, request, current_app, render_template, jsonify
import coloredlogs
import logging
from PIL import Image
from io import BytesIO

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
        impath = current_app.config["RAW_IMG_DIR"] + result["filename"]

        with BytesIO() as output:
            with Image.open(impath) as img:
                img = img.resize((img.width // 2, img.height // 2))
                img.save(output, "JPEG", quality=50)
            data = output.getvalue()

            encoded_string = base64.b64encode(data)
            encoded_string = encoded_string.decode("utf-8")
            images.append({"name": cam, "img": encoded_string})

    return jsonify(images)


@bp.route('/timeline', methods=['POST'])
def timeline():
    data = dict()

    misc = cm.cons["sean"]["activitylearner"].misc
    tl = list()

    if misc is not None:
        segment_times = misc["segment_times"]
        segments = misc["segments"]


        for i in range(len(segments)):
            row = {}
            row["start_time"] = segment_times[i][0]
            row["end_time"] = segment_times[i][1]
            row["count"] = misc["segments"][i][1] - misc["segments"][i][0]
            tl.append(row)

    data["time_range"] = misc["time_range"]
    data["timeline"] = tl
    return jsonify(data)


@bp.route('/knowledge', methods=['POST'])
def knowledge():
    data = dict()
    #labels = ["勉強", "睡眠", "食事", "テレビ", "パソコン", "スマホ", "読書", "留守"]

    al = cm.cons["sean"]["activitylearner"]
    misc = al.misc

    if misc is not None:
        #mapping = misc["train_labels"]["activity"]["mapping"]
        intervals = misc["train_labels"]["activity"]["intervals"]
        labels = al.labels
        classes = list(set(labels))
        data["classes"] = classes
        label_indices = []

        icons = []
        for label, (start, end) in zip(labels, intervals):
            mid = (start + end) // 2
            cam_num = 1
            d = misc["raw_data"][mid][cam_num]
            impath = current_app.config["RAW_IMG_DIR"] + d["filename"]

            with BytesIO() as output:
                with Image.open(impath) as img:
                    img = img.resize((img.width // 2, img.height // 2))
                    img.save(output, "JPEG", quality=50)
                bytedata = output.getvalue()

                encoded_string = base64.b64encode(bytedata)
                encoded_string = encoded_string.decode("utf-8")
                icons.append(encoded_string)
                label_indices.append(classes.index(label))

        data["icons"] = icons
        data["mapping"] = label_indices
    else:
        data["classes"] = []
        data["icons"] = []
        data["mapping"] = []

    return jsonify(data)