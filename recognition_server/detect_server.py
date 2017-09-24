import flask
import scipy.misc
import sys
import uuid

from flask import Flask, render_template, request
app = Flask(__name__)

#from flask.ext.cors import CORS, cross_origin
#cors = CORS(app)
#app.config['CORS_HEADERS'] = 'Content-Type'

import re
import os
import json
from PIL import Image
import numpy as np
from io import BytesIO
import cv2
import tracker
import colorsys
import random

#if len(sys.argv) == 2 and sys.argv[1] == "ssd":
#    import ssd as nn
#else:
import rcnn2 as nn

#from OpenSSL import SSL

#context = SSL.Context(SSL.SSLv23_METHOD)
#cer = os.path.join(os.path.dirname(__file__), 'bacchus_rcnn.crt')
#key = os.path.join(os.path.dirname(__file__), 'bacchus_rcnn.key')

@app.route('/detect_dataurl', methods=['POST'])
#@cross_origin()
def process_image_dataurl():
    data = request.form["image_data"]
    data = str(data.split(",")[1])
    im = Image.open(BytesIO(data.decode('base64')))
    im.save("image.png")

    dets, image = detect()

    return dets

def format_image(image):
    #image = np.array(Image.open("image.png"))
    
    if len(image.shape) == 2:
        image = np.expand_dims(image, 2)
        image = np.repeat(image, 3, 2)
    elif image.shape[2] > 3:
        image = image[:, :, :3]
    elif image.shape[2] == 1:
        image = np.repeat(image, 3, 2)

    return image

def visualize(frame, all_boxes, win_name="frame"):
    for result in all_boxes["objects"]:
        det = result["box"]
        name = result["label"]

        i = sum([ord(x) for x in name])
        c = colorsys.hsv_to_rgb(i%100.0/100.0, 1.0, 0.9)
        c = tuple([int(x * 255.0) for x in c])
        cv2.putText(frame, name, (det[0], det[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, c, 2)
        cv2.rectangle(frame, (det[0], det[1]), (int(det[2]), int(det[3])), c, 2)

    #cv2.imshow(win_name, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
    #cv2.waitKey(1)

clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))

def preprocess(img):
    print(img.shape)
    img_yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
    img_yuv[:,:,0] = clahe.apply(img_yuv[:,:,0])
    img_output = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2RGB)

    #img_output = cv2.fastNlMeansDenoisingColored(img_output,None,5,5,7,21)

    #cv2.imwrite('image.png', img_output)
    return img_output

track = tracker.Tracker()

# parameters to tweak
# tracker remove and add threshold
# detector confidence and nms threshold

def process_image(imgmat, data):
    thres = 0.3
    get_img_feats = False
    get_obj_feats = False
    get_obj_dets = True
    
    imgmat = preprocess(imgmat)
    if "threshold" in data:
        thres = float(data["threshold"])
    if "get_image_features" in data:
        get_img_feats = data["get_image_features"] == "true"
    if "get_object_detections" in data:
        get_obj_dets = data["get_object_detections"] == "true"
    if "get_object_features" in data:
        get_obj_feats = data["get_object_features"] == "true"

    only_img_feats = get_img_feats and not get_obj_feats and not get_obj_dets

    print("detecting...")
    imgmat = format_image(imgmat)
    out = nn.detect(imgmat, thres, only_img_feats)
    print("detected")

    out_data = {}
    img_feats, obj_dets, obj_feats = out
    objs = [{} for _ in range(len(obj_dets))]

    if get_img_feats:
        fn = str(uuid.uuid4()) + ".npy"
        np.save("../main_server/hai/image_features/" + fn, img_feats)
        out_data["image_features_filename"] = fn

    if get_obj_feats:
        fn = str(uuid.uuid4()) + ".npy"
        np.save("../main_server/hai/object_features/" + fn, np.array(obj_feats))
        out_data["object_features_filename"] = fn

    if get_obj_dets:
        for i, det in enumerate(obj_dets):
            det["list_index"] = i
            objs[i].update(det)
        out_data["detections"] = objs
    
    return out_data

@app.route('/detect', methods=["POST"])
#@cross_origin()
def detect_send_image():
    f = request.files["image"]

    fname = "/tmp/{}.png".format(random.randint(0,10000000))

    f.save(fname)

    imgmat = cv2.imread(fname)

    data = request.form.to_dict()

    out_data = process_image(imgmat, data)

    #visualize(imgmat, dets)

    os.remove(fname)

    #visualize(cv2.imread('image.png'), clean_dets, "clean")

    return json.dumps(out_data)

@app.route('/detect_path', methods=["POST"])
def detect_path_image():
    data = request.form.to_dict()
    imgmat = cv2.imread(data["path"])
    out_data = process_image(imgmat, data)

    return json.dumps(out_data)

if __name__ == "__main__":
    #context = (cer, key)
    try:
        app.run(host='0.0.0.0', threaded=False, use_reloader=False, debug=True, port=5002)
    except KeyboardInterrupt:
        print("closing")
