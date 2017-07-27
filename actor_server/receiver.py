import zerorpc
import imagedb
import os
import _thread as thread
import cv2
import numpy as np
import json
from PIL import Image
import datetime
from actions.doer import do_action
import requests

CLEAR_IMGS = True
VISUALIZE = False

image_dir = "../captures"
img_paths = []

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--detect_ip", default="localhost")
args = parser.parse_args()

class HelloRPC(object):
    def newimage(self, path):
        #print("new image: {}".format(path))

        img_paths.append(path)

        return "ok"#str(mean)

    def new_act(self, data):
        data = json.loads(data)
        print(data)
        do_action(data["app"], data["action"])
        requests.post("http://localhost:5003/rebuild")
        return "ok"

#if CLEAR_IMGS:
#    print("deleting {} images".format(len(os.listdir(image_dir))))
#    for f in os.listdir(image_dir):
#        os.remove(os.path.join(image_dir, f))

def detect(path):
    r = requests.post("http://{}:5002/detect".format(args.detect_ip), files={'image': open(path, "rb")})
    
    return json.loads(r.text)

def control(state):
    r = requests.post("http://localhost:5003/control", json={'state': state})
    
    if r == "null":
        return None
    else:
        return json.loads(r.text) 

def update_loop():
    try:
        while True:
            update()
    except KeyboardInterrupt:
        clear_imgs()

def clear_imgs():
    while len(img_paths) > 0:
        path = img_paths.pop()
        p = os.path.join(image_dir, path)
        if os.path.isfile(p):
            os.remove(p)

def update():
    if len(img_paths) > 0:
            latest_img = img_paths.pop()
            
            if CLEAR_IMGS:
                clear_imgs()
            
            if os.path.isfile(latest_img):
                print(latest_img)
                error = False

                try:
                    dets = detect(latest_img)
                except:
                    error = True

                os.remove(latest_img)

                if error:
                    print("server error")
                    return

                ms = int(latest_img.split("/")[-1][:-4])
                d = datetime.datetime.utcfromtimestamp(ms/1000.0)

                state = {"path": latest_img, "time": ms, "detections": dets}

                state_db = dict(state)
                state_db["time"] = d
                imagedb.save(state_db)

                try:
                    act = control(state)

                    if act is not None:
                        for a in act:
                            do_action(a["app"], a["cmd"])
                except Exception as e:
                    print(e)
                    print("no response from control server")

                if VISUALIZE:
                    img = Image.open(latest_img)
                    canvas = np.array(img)#np.zeros([img.size[1], img.size[0], 3], dtype=np.uint8)

                    for obj in json.loads(dets):
                        box = obj["box"]
                        c = (0, 255, 0)

                        if obj["label"] == "person":
                            c = (255, 0, 0)

                        canvas = cv2.rectangle(canvas, (box[0], box[1]), (box[2], box[3]), c, 3)

                    cv2.imshow("frame.png", canvas[..., [2, 1, 0]])
                    cv2.waitKey(1)

thread.start_new_thread(update_loop, ())
s = zerorpc.Server(HelloRPC())
s.bind("tcp://0.0.0.0:5001")
s.run()
