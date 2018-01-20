import base64, os
import time

from flask import Blueprint, request, current_app, render_template, jsonify
import coloredlogs
import logging
from PIL import Image
from io import BytesIO
import numpy as np

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
        data["classes"] = al.classes
    else:
        data["predictions"] = []
        data["images"] = []
        data["classes"] = []

    return jsonify(data)


def points2segments(predictions, times, cam_segments):
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
    label_data = [{"time": r["time"], "label": r["label"]} for r in label_data]
    data["predictions"] = []
    data["confidences"] = []
    data["time_range"] = []
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
        step = 10

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

            encoded_string = impath2base64(impath)
            icons.append(encoded_string)
            label_indices.append(classes.index(label))

        data["icons"] = icons
        data["mapping"] = label_indices
    else:
        data["classes"] = []
        data["icons"] = []
        data["mapping"] = []

    return jsonify(data)