import zerorpc
import imageparser
import imagedb
import os
import _thread as thread
import cv2
import numpy as np
import json
from PIL import Image
import datetime
import action.baseline1 as baseline1
import action.nn.action_nn as action_nn
from actions.doer import do_action
import requests

CLEAR_IMGS = True
VISUALIZE = False

image_dir = "../hai_server/images/"
img_paths = []

actor = action_nn.NNActor()#baseline1.BaselineActor()

class HelloRPC(object):
    def newimage(self, path):
        #print("new image: {}".format(path))

        img_paths.append(path)

        return "ok"#str(mean)

    def new_act(self, data):
        data = json.loads(data)
        print(data)
        do_action(data["app"], data["action"])
        actor.rebuild()
        return "ok"

if CLEAR_IMGS:
    print("deleting {} images".format(len(os.listdir(image_dir))))
    for f in os.listdir(image_dir):
        os.remove(os.path.join(image_dir, f))

def detect(path):
    r = requests.post("http://localhost:5002/detect", files={'image': open(path, "rb")})
    
    return r.text

def update_loop():
    global img_paths

    while True:
        if len(img_paths) > 0:
            if CLEAR_IMGS:
                for path in img_paths[:-1]:
                    if os.path.isfile(path):
                        os.remove(path)
                
            latest_img = img_paths[-1]
            
            img_paths = []
            
            if os.path.isfile(latest_img):
                dets = detect(latest_img)
                ms = int(latest_img.split("/")[-1][:-4])
                d = datetime.datetime.utcfromtimestamp(ms/1000.0)

                state = {"path": latest_img, "time": d, "detections": dets}

                act = actor.act(state)
                print(act)

                if act is not None:
                    do_action(act[0], act[1])

                imagedb.save(state)

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

            if CLEAR_IMGS:
                for path in os.listdir(image_dir):
                    p = os.path.join(image_dir, path)
                    if os.path.isfile(p):
                        os.remove(p)

thread.start_new_thread(update_loop, ())
s = zerorpc.Server(HelloRPC())
s.bind("tcp://0.0.0.0:5001")
s.run()
