from .controller import Controller
import database as db
import cv2
import colorsys
from server_actors import chatbot
from threading import Timer
import os
import time
import itertools

def chunker(seq, size):
  return (seq[pos:pos+size] for pos in range(0, len(seq), size))

def visualize(frame, summ):
    for result in summ:
        det = result["box"]
 
        if result["label"] == "person" and result["keypoints"] is not None:
          for x, y, c in chunker(list(itertools.chain.from_iterable(result["keypoints"].values())), 3):
            if c > 0.05:
              cv2.circle(frame, (int(x), int(y)), 3, (0, 255, 0), -1)

        name = result["label"] + ": " + "%.2f" % result["confidence"]

        i = sum([ord(x) for x in result["label"]])
        c = colorsys.hsv_to_rgb(i%100.0/100.0, 1.0, 0.9)
        c = tuple([int(x * 255.0) for x in c])
        cv2.putText(frame, name, (det[0], det[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, c, 2)
        cv2.rectangle(frame, (det[0], det[1]), (int(det[2]), int(det[3])), c, 2)

    return frame

def draw(path, summ):
    import hai

    print(os.path.join(hai.app.config["RAW_IMG_DIR"], path))

    img = cv2.imread(hai.app.config["RAW_IMG_DIR"] + path)
    img = visualize(img, summ)

    return img

class Snapshot(Controller):
    def __init__(self, user):
        self.user = user

    def on_event(self, event, data):
        if event == "chat":
            msg = data["message"]["text"]

            if msg == "snapshot":
              n = db.mongo.images.find({"user_name": self.user, "summary":{"$exists": True}
                }).sort([("time",-1)]).limit(1).next()
              path = n["filename"]
              summ = n["summary"]
              print(summ) 
              img = draw(path, summ)

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
