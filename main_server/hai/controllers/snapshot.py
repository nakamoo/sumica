from .controller import Controller
import database as db
import cv2
import colorsys
from server_actors import chatbot
from threading import Timer
import os
import time
import itertools
from controllers import utils

def draw(data):
    import hai

    path = data["filename"]
    summ = data["summary"]

    print(os.path.join(hai.app.config["RAW_IMG_DIR"], path))

    img = cv2.imread(hai.app.config["RAW_IMG_DIR"] + path)
    diff = cv2.imread(hai.app.config["RAW_IMG_DIR"] + data["diff_filename"])
    #print(img.shape, diff.shape)
    diff = cv2.resize(diff, (img.shape[1], img.shape[0]))

    img += diff
    img = utils.visualize(img, summ)

    return img

class Snapshot(Controller):
    def __init__(self, user):
        self.user = user

    def on_event(self, event, data):
        if event == "chat":
            msg = data["message"]["text"].strip()
            cam = 0
            
            if msg.startswith("snapshot"):
              try:
                cam = int(msg.split()[-1])
              except:
                return
              n = db.mongo.images.find({"user_name": self.user, "cam_id": str(cam), "summary":{"$exists": True}
                }).sort([("time",-1)]).limit(1)
              if n.count() <= 0:
                 chatbot.send_fb_message(data["sender"]["id"], "no image, sorry")
                 return
              else:
                 n = n.next()
              img = draw(n)
              path = n["filename"]

              import hai

              print("writing to: ", path)
              cv2.imwrite("./static/" + path, img)
              age = time.time() - float(n["time"])
              chatbot.send_fb_message(data["sender"]["id"], "here's your image ({} secs ago)".format(age))
              url = "http://homeai.ml:{}/static/".format(hai.port) + path
              print("snapshot url:", url)
              chatbot.send_fb_image(data["sender"]["id"], url)
             
              #os.remove("./static/" + path)
              def rem(path):
                os.remove(path)
              Timer(30.0, rem, ("./static/" + path,)).start()


    def execute(self):
        return []
