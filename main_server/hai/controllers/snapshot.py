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
    from _app import app

    path = data["filename"]
    summ = data["summary"]

    print(os.path.join(app.config["RAW_IMG_DIR"], path))

    img = cv2.imread(app.config["RAW_IMG_DIR"] + path)
    diff = cv2.imread(app.config["RAW_IMG_DIR"] + data["diff_filename"])
    #print(img.shape, diff.shape)
    diff = cv2.resize(diff, (img.shape[1], img.shape[0]))

    #img += diff
    img = utils.visualize(img, summ)

    return img

def show_image_chat(n, fb_id, send_img=True, message=""):
    img = draw(n)
    path = n["filename"]

    from _app import app

    print("writing to: ", path)
    img = cv2.putText(img, message, (0, img.shape[0]-100), cv2.FONT_HERSHEY_SIMPLEX, 2,  (0, 255, 0), 2)
    cv2.imwrite("./static/" + path, img)
    age = time.time() - float(n["time"])
    chatbot.send_fb_message(fb_id, "here's your image ({} secs ago)".format(age))
    url = "https://homeai.ml:{}/static/".format(app.config["PORT"]) + path
    chatbot.send_fb_message(fb_id, "(url: {})".format(url))
    print("snapshot url:", url)
    
    if send_img:
        chatbot.send_fb_image(fb_id, url)

    #os.remove("./static/" + path)
    def rem(path):
        os.remove(path)
    #Timer(3600.0, rem, ("./static/" + path,)).start()

class Snapshot(Controller):
    def __init__(self, user):
        self.user = user

    def on_event(self, event, data):
        if event == "chat":
            msg = data["message"]["text"].strip()
            cam = 0
            
            if msg.startswith("snapshot"):
              cam = msg.split()[-1]
              n = db.mongo.images.find({"user_name": self.user, "cam_id": str(cam), "summary":{"$exists": True}
                }).sort([("time",-1)]).limit(1)
              if n.count() <= 0:
                 chatbot.send_fb_message(data["sender"]["id"], "no image, sorry")
                 return
              else:
                 n = n.next()
              show_image_chat(n, data["sender"]["id"])


    def execute(self):
        return []
