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
    args = request.get_json(force=True)
    data = {}

    #username = request.args.get('username')

    al = cm.cons[current_app.config["USER"]]["activitylearner"]

    if al.current_images is not None:
        if args['get_images']:
            images = []

            for i, im in enumerate(al.current_images):
                impath = current_app.config["RAW_IMG_DIR"] + im["filename"]

                encoded_string = impath2base64(impath, meta=im, quality=100)
                images.append({"name": al.cams[i], "img": encoded_string})
            data["images"] = images

        data["predictions"] = al.current_predictions
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

def points2segments(predictions, times, cam_segments, start_index, end_index):
    logger.debug("smoothing...")

    predictions = predictions[start_index:end_index]
    times = times[start_index:end_index]

    predictions = smooth_predictions(predictions, times)
    logger.debug("done " + str(len(predictions)))
    segments = []

    for start_cam, end_cam in cam_segments:
        current = None
        start = None

        if end_cam > start_index:
            seq = predictions[max(0, start_cam-start_index):min(len(predictions),end_cam-start_index)]
            for i, p in enumerate(seq):
                if current != p or i == len(seq)-1:
                    if current is not None:
                        segments.append({
                            "start_time": times[max(0, start_cam-start_index) + start],
                            "end_time": times[max(0, start_cam-start_index) + i],
                            "class": current
                        })
                    start = i

                current = p

    return segments

@bp.route('/timeline', methods=['POST'])
def timeline():
    logger.debug("returning timeline data...")
    data = dict()

    args = request.get_json(force=True)
    start_time = args['start_time']
    end_time = args['end_time']

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
    cam_num = 0

    logger.debug("returning timeline data 2...")

    if misc is not None:
        segment_times = misc["segment_times"]
        segments = misc["segments"]

        print("start time:", start_time)
        print("end segs:", segment_times[0], segment_times[-1])

        for i in range(len(segments)):
            if segment_times[i][1] >= start_time and segment_times[i][0] <= end_time:
                row = {}
                row["start_time"] = segment_times[i][0]
                row["end_time"] = segment_times[i][1]
                row["seg_index"] = i
                row["count"] = misc["segments"][i][1] - misc["segments"][i][0] + 1

                midpoint = (misc["segments"][i][1] + misc["segments"][i][0]) // 2
                imname = misc["raw_data"][midpoint][cam_num]["filename"]
                impath = current_app.config["RAW_IMG_DIR"] + imname
                impath = saveimgtostatic(imname, impath, scale=0.3, quality=50)
                row["img"] = "https://homeai.ml:5000/" + impath

                imgs = []
                startpoint = min(misc["segments"][i][0] + 5, misc["segments"][i][1])
                endpoint = max(misc["segments"][i][1] - 5, misc["segments"][i][1])
                for point in [startpoint, midpoint, endpoint]:
                    imname = misc["raw_data"][point][cam_num]["filename"]
                    impath = current_app.config["RAW_IMG_DIR"] + imname
                    impath = saveimgtostatic(imname, impath, scale=0.5, quality=100)

                    d = {"url": "/" + impath, "time": misc["raw_data"][point][cam_num]["time"],
                         "id": str(misc["raw_data"][point][cam_num]["_id"])}
                    imgs.append(d)

                row["imgs"] = imgs

                tl.append(row)

        data["time_range"] = misc["time_range"]
        data["segments_last_fixed"] = misc["segments_last_fixed"]

    logger.debug("returning timeline data 3...")

    if al.predictions is not None:
        #print("AAA", len(al.predictions), len(misc["times"]), len(misc["cam_segments"]))
        np_times = np.array(misc["times"])
        np_preds = np.array(al.predictions)
        start_index = np.where(np_times >= start_time)[0][0] # first index that is greater than start_time
        end_index = np.where(np_times <= end_time)[0][-1]
        #logger.debug(str(start_index) + " start")
        preds = points2segments(np_preds, np_times, misc["cam_segments"], start_index, end_index)

        #logger.debug("returning timeline data 4...")

        #data_preds = []

        #print(start_time, preds)

        #for i, p in enumerate(preds):
        #    if p["end_time"] >= start_time:
        #        data_preds.append(p)

        data["predictions"] = preds#data_preds
        data["classes"] = al.classes

        times = misc["times"]
        conf = []
        conf_times = []
        step = CONFIDENCE_SMOOTH

        for i, (s, e) in enumerate(misc["cam_segments"]):
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

    logger.debug("returned timeline data.")

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

    if misc is not None and al.classes is not None:
        segs = misc["segments"]
        seg_indices = misc["train_labels"]["activity"]["seg_mapping"]
        labels = al.labels
        data["classes"] = al.classes

        for c in al.classes:
            # class name is id
            data["nodes"].append({"id": c, "type": "label", "text": c})

        for i, label in enumerate(labels[:len(seg_indices)]):
            start, end = segs[seg_indices[i]]
            mid = (start + end) // 2
            cam_num = 0

            d = misc["raw_data"][mid][cam_num]
            impath = current_app.config["RAW_IMG_DIR"] + d["filename"]
            impath = saveimgtostatic(d["filename"], impath, scale=0.2, quality=50)

            imid = str(d["_id"])
            data["nodes"].append({"id": imid, "type": "image", "image": impath})
            data["edges"].append({"source": imid, "source_index": 0, "target": label, "target_index": 0})

        rules = list(db.actions.find())

        for rule in rules:
            data["nodes"].append({"id": str(rule["_id"]), "type": "action", "text": rule["name"], "platform": rule["platform"],
                                  "data": rule["data"]})

            for target_i, inp_pts in enumerate(rule["data"]["inputs"]):
                for source in inp_pts:
                    data["edges"].append({"source": source["id"], "source_index": source["index"], "target": str(rule["_id"]),
                                          "target_index": target_i})

    return jsonify(data)


@bp.route('/label', methods=['POST'])
def change_label():
    al = cm.cons[current_app.config["USER"]]["activitylearner"]
    args = request.get_json(force=True)
    logger.debug(str(args))

    action = args['type']
    username = args['username']

    if action == 'remove':
        id_ = args['id']
        db.labels.delete_one({"_id": ObjectId(id_)})
        logger.debug('removed label')
        al.update = True
    elif action == 'add':
        al.update = True
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

    #cm.cons[username]["ruleexecutor"].update_rules()
    cm.cons[username]["nodemanager"].update_nodes()

    return "ok", 201

@bp.route('/node_states', methods=['POST'])
def node_states():
    nm = cm.cons[current_app.config["USER"]]["nodemanager"]

    if nm.values is None:
        return jsonify([]), 200

    re = dict()
    re["nodes"] = [{"id": k, "values": v} for k, v in nm.values.items()]

    return jsonify(re), 200

@bp.route('/segment-info', methods=['POST'])
def segment_info():
    args = request.get_json(force=True)
    cam_num = 0

    al = cm.cons[current_app.config["USER"]]["activitylearner"]
    misc = al.misc
    imgs = []
    #segment_times = misc["segment_times"]

    seg_index = args["seg_index"]

    #print(args)
    #i = args["index"]
    startpoint = misc["segments"][seg_index][0]
    midpoint = (misc["segments"][seg_index][1] + misc["segments"][seg_index][0]) // 2
    endpoint = misc["segments"][seg_index][1]

    for point in [startpoint, midpoint, endpoint]:
        imname = misc["raw_data"][point][cam_num]["filename"]
        impath = current_app.config["RAW_IMG_DIR"] + imname
        impath = saveimgtostatic(imname, impath, scale=0.3, quality=50)

        imgs.append("/" + impath)

    re = dict()
    re["imgs"] = imgs
    return jsonify(re), 200