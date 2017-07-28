import flask
import scipy.misc
import sys

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

if len(sys.argv) == 2 and sys.argv[1] == "ssd":
    import ssd as nn
else:
    import rcnn as nn

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

def detect():
    image = np.array(Image.open("image.png"))
    
    if len(image.shape) == 2:
        image = np.expand_dims(image, 2)
        image = np.repeat(image, 3, 2)
    elif image.shape[2] > 3:
        image = image[:, :, :3]
    elif image.shape[2] == 1:
        image = np.repeat(image, 3, 2)

    dets = nn.detect(image)

    return dets

def visualize(frame, all_boxes, win_name="frame"):
    for result in all_boxes:
        det = result["box"]
        name = result["label"]

        i = sum([ord(x) for x in name])
        c = colorsys.hsv_to_rgb(i%100.0/100.0, 1.0, 0.9)
        c = tuple([int(x * 255.0) for x in c])
        cv2.putText(frame, name, (det[0], det[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, c, 2)
        cv2.rectangle(frame, (det[0], det[1]), (int(det[2]), int(det[3])), c, 2)

    cv2.imshow(win_name, frame)
    cv2.waitKey(1)

clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))

def preprocess(img):
    img_yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
    img_yuv[:,:,0] = clahe.apply(img_yuv[:,:,0])
    img_output = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)

    #img_output = cv2.fastNlMeansDenoisingColored(img_output,None,5,5,7,21)

    cv2.imwrite('image.png', img_output)

track = tracker.Tracker()

# parameters to tweak
# tracker remove and add threshold
# detector confidence and nms threshold

@app.route('/detect', methods=["POST"])
#@cross_origin()
def process_image():
    f = request.files["image"]

    f.save("image.png")

    preprocess(cv2.imread('image.png'))

    dets = detect()

    visualize(cv2.imread('image.png'), dets)

    clean_dets = track.update(dets)

    visualize(cv2.imread('image.png'), clean_dets, "clean")

    return json.dumps(clean_dets)#json.dumps(dets)

if __name__ == "__main__":
    #context = (cer, key)
    app.run(host='0.0.0.0', threaded=False, use_reloader=False, debug=True, port=5002)
