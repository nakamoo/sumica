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

def object_detection(imgmat, query):
    # default settings
    conf_thresh = 0.3
    get_img_feats = False
    get_obj_feats = False
    get_obj_dets = True
    
    if "detection_threshold" in data:
        conf_thresh = float(data["detection_threshold"])
    if "get_image_features" in data:
        get_img_feats = data["get_image_features"] == "true"
    if "get_object_detections" in data:
        get_obj_dets = data["get_object_detections"] == "true"
    if "get_object_features" in data:
        get_obj_feats = data["get_object_features"] == "true"

    only_img_feats = get_img_feats and not get_obj_feats and not get_obj_dets

    # if only_img_feats, RCNN will only do region proposal step
    out = detection_nn.detect(imgmat, conf_thresh, only_img_feats)

    out_data = {}
    img_feats, obj_dets, obj_feats = out
    objs = [{} for _ in range(len(obj_dets))]

    if get_img_feats:
        fn = str(uuid.uuid4()) + ".npy"
        #print("img", img_feats.shape)
        np.save("../main_server/hai/image_features/" + fn, np.max(img_feats, axis=(0,1)))
        out_data["image_features_filename"] = fn

    if get_obj_feats:
        fn = str(uuid.uuid4()) + ".npy"
        obj_feats = np.array(obj_feats)
        #print("obj", obj_feats.shape)
        np.save("../main_server/hai/object_features/" + fn, obj_feats)
        out_data["object_features_filename"] = fn

    if get_obj_dets:
        for i, det in enumerate(obj_dets):
            det["list_index"] = i
            objs[i].update(det)
        out_data["detections"] = objs
    
    return out_data

@app.route('/extract_features', methods=["POST"])
def extract_features():
    query = request.form.to_dict()
    imgmat = format_image(io.imread(data["path"]))
    out_data = object_detection(imgmat, query)
    #out_data = pose_estimation(imgmat, out_data)
    #out_data = action_recognition(imgmat, out_data)

    return json.dumps(out_data)

if __name__ == "__main__":
    app.run(host='0.0.0.0', threaded=False, use_reloader=False, debug=True, port=5002)
