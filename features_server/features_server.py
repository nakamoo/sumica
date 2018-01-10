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

import PyOpenPose as OP
from concurrent.futures import ThreadPoolExecutor, wait

def init_pose():
    op = OP.OpenPose((656, 368), (368, 368), (1280, 720), "COCO", "/home/sean/openpose/models/", 0, False,
                OP.OpenPose.ScaleMode.ZeroToOne, True, True)
    return op

# GPU conflict somehow goes away when using threads
pose_executor = ThreadPoolExecutor(1)
future = pose_executor.submit(init_pose)
wait([future])
op = future.result()

import detection_nn

from i3dnn import I3DNN
i3d = I3DNN("2")

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

def pose_estimation(img):
    op.detectPose(img)
    op.detectFace(img)
    op.detectHands(img)
    body = op.getKeypoints(op.KeypointType.POSE)[0]
    hand = op.getKeypoints(op.KeypointType.HAND)[0]
    face = op.getKeypoints(op.KeypointType.FACE)[0]
    new_data = {'body': [], 'hand': [], 'face': []}

    if body is not None:
        new_data['body'] = body.tolist()
                
    if hand is not None:
        new_data['hand'] = hand.tolist()
                
    if face is not None:
        new_data['face'] = face.tolist()
        
    return new_data

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

def action_recognition(whole_img, data):
    for i in range(len(data["detections"])):
                if data["detections"][i]["label"] == "person":
                        box = data["detections"][i]["box"]
                        longer_side = max((box[2]-box[0])*2.0,(box[3]-box[1])*2.0)
                        longer_side = min(min(whole_img.shape[1], longer_side), whole_img.shape[0])
                            
                        a = int(longer_side/2)
                        cx, cy = (box[0]+box[2])//2, (box[1]+box[3])//2
                        x1, y1, x2, y2 = cx-a, cy-a, cx+a, cy+a
                        if x1 < 0:
                            x2 -= x1
                            x1 = 0
                        if y1 < 0:
                            y2 -= y1
                            y1 = 0
                        if x2 >= whole_img.shape[1]:
                            x1 -= x2-whole_img.shape[1]
                            x2 = whole_img.shape[1]
                        if y2 >= whole_img.shape[0]:
                            y1 -= y2-whole_img.shape[0]
                            y2 = whole_img.shape[0]
                            
                        crop = whole_img[y1:y2,x1:x2,:]
                        crop = cv2.resize(crop, (224, 224))
                        img = np.array([[crop for _ in range(10)]])
                        prob, logits, label, feats = i3d.process_image(img)
                        det = data["detections"][i]
                        updates = {}
                        updates["action_label"] = label
                        updates["action_confidence"] = float(prob)
                        updates["action_crop"] = [x1,y1,x2,y2]
                        updates["action_vector"] = feats
                        det.update(updates)
                        
                        #a = persons.index(i)
                        #if pose_indices[a] is not None:
                        #    updates["detections.{}.pose_body_index".format(i)] = pose_indices[a]
                        
    return data

@app.route('/extract_features', methods=["POST"])
def extract_features():
    query = request.form.to_dict()
    imgmat = format_image(io.imread(query["path"]))
    
    out_data = object_detection(imgmat, query)
    
    future = pose_executor.submit(pose_estimation, (imgmat))
    wait([future])
    pose_data = future.result()
    
    out_data["pose"] = pose_data
    out_data = action_recognition(imgmat, out_data)

    return json.dumps(out_data)

if __name__ == "__main__":
    app.run(host='0.0.0.0', threaded=False, use_reloader=False, debug=False, port=5002)
