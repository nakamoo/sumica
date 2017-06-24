import zerorpc
import imageparser
import imagedb
import os
import thread
import cv2
import numpy as np
import json
from PIL import Image
import datetime
import baseline1

CLEAR_IMGS = True
VISUALIZE = True

image_dir = "../hai_server2/images"
img_paths = []

actor = baseline1.Actor()

class HelloRPC(object):
    def newimage(self, path):
        #print("new image: {}".format(path))

        img_paths.append(path)

        return "ok"#str(mean)

    def newcommand(self, cmd):
        actor.rebuild()
        return "ok"

if CLEAR_IMGS:
    print("deleting {} images".format(len(os.listdir(image_dir))))
    for f in os.listdir(image_dir):
        os.remove(os.path.join(image_dir, f))

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
                dets = imageparser.detect(latest_img)
                ms = int(latest_img.split("/")[-1][:-4])
                d = datetime.datetime.utcfromtimestamp(ms/1000.0)

                state = {"path": path, "time": d, "detections": dets}

                actor.act(state)

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
                    p = os.path.join(image_dir, f)
                    if os.path.isfile(p):
                        os.remove(p)

thread.start_new_thread(update_loop, ())
s = zerorpc.Server(HelloRPC())
s.bind("tcp://0.0.0.0:5001")
s.run()