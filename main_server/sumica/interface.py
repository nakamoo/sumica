import base64, os
import time

from flask import Blueprint, request, current_app, render_template, jsonify
import coloredlogs
import logging
from PIL import Image
from io import BytesIO
import numpy as np
from scipy import stats
from bson.objectid import ObjectId

from utils import db
from controllers.utils import impath2base64, saveimgtostatic
import controllermanager as cm

logger = logging.getLogger(__name__)
coloredlogs.install(level=current_app.config['LOG_LEVEL'], logger=logger)

bp = Blueprint("interface", __name__)

PREDICTION_SMOOTH = 10
CONFIDENCE_SMOOTH = 30


@bp.route('/interface', methods=['GET'])
def interface():
    username = request.args.get('username')

    return render_template('interface.html')

@bp.route('/feed', methods=['POST'])
def feed():
    data = {}

    #username = request.args.get('username')

    al = cm.cons[current_app.config["USER"]]["activitylearner"]

    if al.current_images is not None:
        images = []

        for i, im in enumerate(al.current_images):
            impath = current_app.config["RAW_IMG_DIR"] + im["filename"]

            encoded_string = impath2base64(impath)
            images.append({"name": al.cams[i], "img": encoded_string})

        data["predictions"] = al.current_predictions
        data["images"] = images
    else:
        data["predictions"] = []
        data["images"] = []

    if al.classes is not None:
        data["classes"] = al.classes
    else:
        data["classes"] = []

    return jsonify(data)

def smooth_predictions(predictions, times):
    preds = np.array(predictions)
    times = np.array(times)
    #smooth = []
    data = []
    k = PREDICTION_SMOOTH

    for i in range(len(preds)):
        start = max(0, i-k)
        end = min(len(preds), i+k)
        x = preds[start:end]

        if len(x) < k*2:
            if start == 0:
                x = np.pad(x, (k*2-len(x), 0), 'edge')
            else:
                x = np.pad(x, (0, k*2-len(x)), 'edge')

        data.append(x)

    modes = stats.mode(data, axis=1)[0]

    return modes.tolist()

def points2segments(predictions, times, cam_segments):
    predictions = smooth_predictions(predictions, times)
    segments = []

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

    args = request.get_json(force=True)
    start_time = args['start_time']

    al = cm.cons[current_app.config["USER"]]["activitylearner"]
    misc = al.misc
    tl = list()

    label_data = al.label_data
    label_data = [{"time": r["time"], "label": r["label"], "id": str(r["_id"])} for r in label_data]
    data["predictions"] = []
    data["confidences"] = []
    data["time_range"] = []
    data["classes"] = []
    data["segments_last_fixed"] = 0

    if misc is not None:
        segment_times = misc["segment_times"]
        segments = misc["segments"]

        for i in range(len(segments)):
            if segment_times[i][1] >= start_time:
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

        data["time_range"] = misc["time_range"]
        data["segments_last_fixed"] = misc["segments_last_fixed"]

    if al.predictions is not None:
        preds = points2segments(al.predictions, misc["times"], misc["cam_segments"])
        data_preds = []

        for i, p in enumerate(preds):
            if p["end_time"] >= start_time:
                data_preds.append(p)

        data["predictions"] = data_preds
        data["classes"] = al.classes

        times = misc["times"]
        conf = []
        conf_times = []
        step = CONFIDENCE_SMOOTH

        for s, e in misc["cam_segments"]:
            if times[e - 1] >= start_time:
                seg = []
                tseg = []
                block = al.confidences[s:e]
                seg.append(block[0])
                tseg.append(times[s])

                for i in range(step, len(block), step):
                    seg.append(np.mean(block[max(0, i - step):i]))
                    tseg.append(times[s + i])

                seg.append(block[-1])
                tseg.append(times[e - 1])

                conf.append(seg)
                conf_times.append(tseg)

        data["confidences"] = conf
        data["conf_times"] = conf_times

    data["timeline"] = tl
    data["label_data"] = label_data

    return jsonify(data)


@bp.route('/knowledge', methods=['POST'])
def knowledge():
    data = dict()
    #labels = ["勉強", "睡眠", "食事", "テレビ", "パソコン", "スマホ", "読書", "留守"]

    al = cm.cons[current_app.config["USER"]]["activitylearner"]
    misc = al.misc

    data["classes"] = []
    data["nodes"] = []
    data["edges"] = []

    if misc is not None:
        segs = misc["segments"]
        seg_indices = misc["train_labels"]["activity"]["seg_mapping"]
        labels = al.labels
        data["classes"] = al.classes

        for c in al.classes:
            # class name is id
            data["nodes"].append({"id": c, "type": "label", "text": c})

        for i, label in enumerate(labels):
            start, end = segs[seg_indices[i]]
            mid = (start + end) // 2
            cam_num = 0

            d = misc["raw_data"][mid][cam_num]
            impath = current_app.config["RAW_IMG_DIR"] + d["filename"]
            impath = saveimgtostatic(d["filename"], impath, scale=0.2, quality=50)

            imid = str(d["_id"])
            data["nodes"].append({"id": imid, "type": "image", "image": impath})
            data["edges"].append({"source": imid, "target": label})

        rules = list(db.actions.find())

        for rule in rules:
            data["nodes"].append({"id": str(rule["_id"]), "type": "action", "text": rule["name"], "data": rule["data"]})

            for inp in rule["data"]["inputs"]:
                data["edges"].append({"source": inp, "target": str(rule["_id"])})

    return jsonify(data)


@bp.route('/label', methods=['POST'])
def change_label():
    args = request.get_json(force=True)
    logger.debug(str(args))

    action = args['type']
    username = args['username']

    if action == 'remove':
        id_ = args['id']
        db.labels.delete_one({"_id": ObjectId(id_)})
        logger.debug('removed label')
    elif action == 'add':
        db.labels.insert_one({"_id": ObjectId(args['id']), "username": username,
                              "time": args['time'], "label": args['label']})
        logger.debug('added label')

    return "ok", 201

@bp.route('/action', methods=['POST'])
def change_action():
    args = request.get_json(force=True)
    logger.debug(str(args))

    action = args['type']
    username = args['username']

    if action == 'remove':
        id_ = args['id']
        db.actions.delete_one({"_id": ObjectId(id_)})
        logger.debug('removed action')
    elif action == 'add':
        db.actions.insert_one({"_id": ObjectId(args['id']), "username": username,
                              "creation_time": time.time(), "name": args['name'],
                               "platform": args['platform'], "data": args['data']})
    elif action == 'update':
        db.actions.update_one({"_id": ObjectId(args['id'])}, {"$set": {
            "name": args['name'],
            "platform": args['platform'], "data": args['data']
        }}, upsert=False)

    cm.cons[username]["ruleexecutor"].update_rules()

    return "ok", 201