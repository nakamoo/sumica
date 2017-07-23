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

    dets, image = nn.detect(image, get_image=True)

    return json.dumps(dets), image

@app.route('/detect', methods=["POST"])
#@cross_origin()
def process_image():
    f = request.files["image"]

    f.save("image.png")
    dets, image = detect()

    return dets

if __name__ == "__main__":
    #context = (cer, key)
    app.run(host='localhost', threaded=False, use_reloader=False, debug=True, port=5002)
