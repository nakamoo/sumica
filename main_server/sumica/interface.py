import base64, os
import time

from flask import Blueprint, request, current_app, render_template, jsonify
import coloredlogs
import logging
from PIL import Image
from io import BytesIO

from utils import db
from controllers.utils import impath2base64, saveimgtostatic
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
    query = {"user_name": current_app.config["USER"], "time": {"$gt": start_time, "$lt": end_time}}
    results = db.images.find(query)
    cams = results.distinct("cam_id")
    cams.sort()

    for cam in cams:
        query = {"user_name": current_app.config["USER"], "time": {"$gt": start_time, "$lt": end_time}, "cam_id": cam}
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


def points2segments(predictions, times, cam_segments):
    segments = []

    logger.debug(str(cam_segments))

    for start_cam, end_cam in cam_segments:
        current = None
        start = None

        seq = predictions[start_cam:end_cam]
        for i, p in enumerate(seq):
            if current != p or i == len(seq)-1:
                if current is not None:
                    segments.append({
                        "start_time": times[start_cam + start],
                        "end_time": times[start_cam + i],
                        "class": current
                    })
                start = i

            current = p

    return segments

@bp.route('/timeline', methods=['POST'])
def timeline():
    data = dict()

    al = cm.cons[current_app.config["USER"]]["activitylearner"]
    misc = al.misc
    tl = list()

    label_data = al.label_data
    label_data = [{"time": r["time"], "label": r["label"]} for r in label_data]
    data["predictions"] = []
    data["time_range"] = []
    data["segments_last_fixed"] = 0

    if misc is not None:
        segment_times = misc["segment_times"]
        segments = misc["segments"]

        for i in range(len(segments)):
            row = {}
            row["start_time"] = segment_times[i][0]
            row["end_time"] = segment_times[i][1]
            row["count"] = misc["segments"][i][1] - misc["segments"][i][0] + 1

            midpoint = (misc["segments"][i][1] + misc["segments"][i][0]) // 2
            imname = misc["raw_data"][midpoint][0]["filename"]
            impath = current_app.config["RAW_IMG_DIR"] + imname
            impath = saveimgtostatic(imname, impath, scale=0.2, quality=50)
            row["img"] = "https://homeai.ml:5000/" + impath

            tl.append(row)

        data["predictions"] = points2segments(al.predictions, misc["times"], misc["cam_segments"])
        data["classes"] = al.classes
        data["confidences"] = al.confidences[::100]
        data["times"] = misc["times"][::100]

        data["time_range"] = misc["time_range"]
        data["segments_last_fixed"] = misc["segments_last_fixed"]

    data["timeline"] = tl
    data["label_data"] = label_data

    return jsonify(data)


@bp.route('/knowledge', methods=['POST'])
def knowledge():
    data = dict()
    #labels = ["勉強", "睡眠", "食事", "テレビ", "パソコン", "スマホ", "読書", "留守"]

    al = cm.cons[current_app.config["USER"]]["activitylearner"]
    misc = al.misc

    if misc is not None:
        #mapping = misc["train_labels"]["activity"]["mapping"]
        intervals = misc["segments"]
        labels = al.labels
        classes = list(set(labels))
        data["classes"] = classes
        label_indices = []

        icons = []
        for label, (start, end) in zip(labels, intervals):
            mid = (start + end) // 2
            cam_num = 0
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