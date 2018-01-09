import flask
import scipy.misc
import sys
import uuid

from flask import Flask, request
app = Flask(__name__)

import re
import os
import json
from skimage import io
import numpy as np
from io import BytesIO
import cv2

import detection_nn

datafiles_root = "../main_server/sumica/datafiles"

def format_image(image):
    if len(image.shape) == 2: # grayscale -> 3 channels
        image = np.expand_dims(image, 2)
        image = np.repeat(image, 3, 2)
    elif image.shape[2] > 3: # 4-channel -> 3-channels
        image = image[:, :, :3]
    elif image.shape[2] == 1: # single-channel -> 3-channelS
        image = np.repeat(image, 3, 2)

    return image

clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))

def preprocess(imgmat):
    img_yuv = cv2.cvtColor(imgmat, cv2.COLOR_RGB2YUV)
    img_yuv[:,:,0] = clahe.apply(img_yuv[:,:,0])
    img_output = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2RGB)

    return img_output

def nms(dets, iou_threshold=0.5):
    sorted_list = sorted(dets, key=lambda k: k['confidence'])
    filtered_list = []

    for det in dets:
        skip = False
        for b in filtered_list:
            if b["label"] == det["label"] and iou(b["box"], det["box"]) > iou_threshold:
                skip = True
                break

        if not skip:
            filtered_list.append(det)

    return filtered_list

def iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    # compute the area of intersection rectangle
    interArea = (xB - xA + 1) * (yB - yA + 1)

    # compute the area of both the prediction and ground-truth
    # rectangles
    boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
    boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)

    # compute the intersection over union by taking the intersection
    # area and dividing it by the sum of prediction + ground-truth
    # areas - the interesection area
    iou = interArea / float(boxAArea + boxBArea - interArea)

    # return the intersection over union value
    return iou

def object_detection(imgmat, query):
    # default settings
    conf_thresh = 0.3
    get_img_feats = False
    get_obj_feats = False
    get_obj_dets = True
    
    if "detection_threshold" in query:
        conf_thresh = float(query["detection_threshold"])
    if "get_image_features" in query:
        get_img_feats = query["get_image_features"] == "true"
    if "get_object_detections" in query:
        get_obj_dets = query["get_object_detections"] == "true"
    if "get_object_features" in query:
        get_obj_feats = query["get_object_features"] == "true"

    only_img_feats = get_img_feats and not get_obj_feats and not get_obj_dets

    # if only_img_feats, RCNN will only do region proposal step
    out = detection_nn.detect(imgmat, conf_thresh, only_img_feats)

    out_data = {}
    img_feats, obj_dets, obj_feats = out

    if get_img_feats:
        fn = str(uuid.uuid4()) + ".npy"
        feats = np.max(img_feats, axis=(0,1)) # collapse feature maps into vector
        np.save(datafiles_root + "/image_features/" + fn, feats)
        out_data["image_features_filename"] = fn

    if get_obj_feats:
        fn = str(uuid.uuid4()) + ".npy"
        obj_feats = np.array(obj_feats)
        np.save(datafiles_root + "/object_features/" + fn, obj_feats)
        out_data["object_features_filename"] = fn

    if get_obj_dets:
        if "nms_threshold" in query:
            out_data["detections"] = nms(obj_dets, float(query["nms_threshold"]))
        else:
            out_data["detections"] = obj_dets
    
    return out_data

@app.route('/extract_features', methods=["POST"])
def extract_features():
    query = request.form.to_dict()
    imgmat = format_image(io.imread(query["path"]))
    out_data = object_detection(imgmat, query)
    #out_data = pose_estimation(imgmat, out_data)
    #out_data = action_recognition(imgmat, out_data)

    return json.dumps(out_data)

if __name__ == "__main__":
    app.run(host='0.0.0.0', threaded=False, use_reloader=False, debug=True, port=5002)
