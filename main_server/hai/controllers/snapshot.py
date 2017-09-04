from .controller import Controller
import database as db
import cv2
import colorsys
from server_actors import chatbot
from threading import Timer
import os
import time
import itertools
import controllers.utils as utils

def visualize(frame, summ):
    for result in summ:
        det = result["box"]
 
        if result["label"] == "person" and result["keypoints"] is not None:
          def draw_pts(pts, col):
            for x, y, c in utils.chunker(pts, 3):
              if c > 0.05:
                cv2.circle(frame, (int(x), int(y)), 3, col, -1)
          
          draw_pts(result["keypoints"]["pose_keypoints"], (0, 255, 0))
          draw_pts(result["keypoints"]["hand_left_keypoints"], (255, 0, 0))
          draw_pts(result["keypoints"]["hand_right_keypoints"], (255, 0, 0))

        name = result["label"] + ": " + "%.2f" % result["confidence"]

        i = sum([ord(x) for x in result["label"]])
        c = colorsys.hsv_to_rgb(i%100.0/100.0, 1.0, 0.9)
        c = tuple([int(x * 255.0) for x in c])
        cv2.putText(frame, name, (det[0], det[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, c, 2)
        cv2.rectangle(frame, (det[0], det[1]), (int(det[2]), int(det[3])), c, 2)

    return frame

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
    img = visualize(img, summ)

    return img

class Snapshot(Controller):
    def __init__(self, user):
        self.user = user

    def on_event(self, event, data):
        if event == "chat":
            msg = data["message"]["text"].strip()
            cam = 0
            
            if msg.startswith("snapshot"):
              if msg.split()[-1].isdigit():
                 cam = int(msg.split()[-1])
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
