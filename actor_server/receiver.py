import zerorpc
import db
import os
import _thread as thread
import cv2
import numpy as np
import json
from PIL import Image
import datetime
from actions.doer import do_action
import requests
import subprocess
import time
from apps.hello import hello
from apps.learner import baseline2

CLEAR_IMGS = True
VISUALIZE = False

image_dir = "../captures"
img_paths = []

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--detect_ip", default="localhost")
args = parser.parse_args()

apps = [hello.HelloActor(), baseline2.LearningActor()]

class HelloRPC(object):
    def newimage(self, path):
        #print("new image: {}".format(path))

        img_paths.append(path)

        return "ok"#str(mean)

    def new_act(self, data):
        data = json.loads(data)
        print(data)
        do_action(data["app"], data["action"])

        for app in apps:
            app.new_action(data)

        # requests.post("http://localhost:5003/rebuild")
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

def visualize_detections(latest_img, dets):
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

def update():
    if len(img_paths) > 0:
        # latest path in buffer
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
                print("recognition server error")
                return

            ms = int(latest_img.split("/")[-1][:-4])
            utc = datetime.datetime.utcfromtimestamp(ms/1000.0)

            """
            from_zone = tz.tzutc()
            to_zone = tz.tzlocal()
            utc = utc.replace(tzinfo=from_zone)
            local = utc.astimezone(to_zone)
            """

            state = {"path": latest_img, "utc_time": ms, "detections": dets}

            state_db = dict(state)
            state_db["utc_time"] = utc
            #state_db["local_time"] = local
            db.save_image_data(state_db)

            if VISUALIZE: # old code; probably has error
                visualize_detections()

            #=================================================

            act = []
            # select actions (iterate through apps)
            for app in apps:
                act.extend(app.act(state))

            # execute actions
            for a in act:
                do_action(a["app"], a["cmd"])

# get state of Philips Hue every n seconds
def get_hue_loop():
    while True:
        # >= Python 3.5
        #result = subprocess.run(['node', 'actions/hue.js', 'get_state'], stdout=subprocess.PIPE)
        #state = json.loads(result.stdout.decode('utf-8'))
        time.sleep(10)

        out = subprocess.check_output(['node', 'actions/hue.js', 'get_state'])
        state = json.loads(out.decode('utf-8'))

        for light in state["lights"]:
            if light["state"]["reachable"]:
                data = light
                data["utc_time"] = datetime.datetime.utcfromtimestamp(time.time())
                apps[1].new_state(data)
                db.save_hue_data(data)
                print("saved hue data.")
                apps[1].update(data)

                break

# get state of Youtube every n seconds
def get_youtube_loop():
    while True:
        time.sleep(10)

        command = "chrome-cli list links | grep www.youtube.com"
        proc = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_data, stderr_data = proc.communicate()
        links = stdout_data.decode('ascii')

        if not links == '':
            while True:
                start = links.find('http')
                end = links.find('\n')
                if start != -1 and end != 1:
                    link = links[start: end]
                    data = {}
                    data["time"] = datetime.datetime.utcfromtimestamp(time.time())
                    data['app'] = "youtube"
                    data['link'] = link
                    db.save_youtube_data(data)
                    links = links[end + 1:]
                else:
                    break

thread.start_new_thread(update_loop, ())
thread.start_new_thread(get_hue_loop, ())
thread.start_new_thread(get_youtube_loop, ())
s = zerorpc.Server(HelloRPC())
s.bind("tcp://0.0.0.0:5001")
s.run()
