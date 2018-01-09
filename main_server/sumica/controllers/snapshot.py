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
    #summ = data["summary"]

    print(os.path.join(app.config["RAW_IMG_DIR"], path))

    img = cv2.imread(app.config["RAW_IMG_DIR"] + path)
    diff = cv2.imread(app.config["RAW_IMG_DIR"] + data["diff_filename"])
    #print(img.shape, diff.shape)
    diff = cv2.resize(diff, (img.shape[1], img.shape[0]))

    #img += diff
    img = utils.visualize(img, data)

    return img

def show_image_chat(n, fb_id, send_img=True, message=""):
    img = draw(n)
    path = n["filename"]

    from _app import app

    print("writing to: ", path)
    img = cv2.putText(img, message, (0, img.shape[0]-100), cv2.FONT_HERSHEY_SIMPLEX, 2,  (0, 255, 0), 2)
    cv2.imwrite("./static/" + path, img)
    age = time.time() - float(n["time"])
    chatbot.send_fb_message(fb_id, "here's your image ({:.2f} secs ago)".format(age))
    url = "https://homeai.ml:{}/static/".format(app.config["PORT"]) + path
    chatbot.send_fb_message(fb_id, "(url: {})".format(url))
    chatbot.send_fb_message(fb_id, "action: {}".format(n["action"]))
    print("snapshot url:", url)
    
    if send_img:
        chatbot.send_fb_image(fb_id, url)

    #os.remove("./static/" + path)
    def rem(path):
        os.remove(path)
    #Timer(3600.0, rem, ("./static/" + path,)).start()
    
def show_image_chat_raw(img, fb_id):
    path = str(int(time.time())) + ".png"
    cv2.imwrite("./static/" + path, img[:,:,[2,1,0]])
    from _app import app
    url = "https://homeai.ml:{}/static/".format(app.config["PORT"]) + path
    chatbot.send_fb_image(fb_id, url)
    
    def rem(path):
        os.remove(path)

class Snapshot(Controller):
    def __init__(self, user):
        self.user = user

    def on_event(self, event, data):
        if event == "chat":
            msg = data["message"]["text"].strip()
            sender = data["sender"]["id"]
            
            if msg.startswith("snapshot"):
                cam = msg.split()[-1]
                #n = db.mongo.images.find({"user_name": self.user, "cam_id": str(cam), "summary":{"$exists": True}
                #                         }).sort([("time",-1)]).limit(1)
                n = db.mongo.images.find({"user_name": self.user, "cam_id": str(cam), "pose":{"$exists": True}
                                          , "detections":{"$exists": True}}).sort([("time",-1)]).limit(1)
                if n.count() <= 0:
                    chatbot.send_fb_message(sender, "no image, sorry")
                    return
                else:
                    n = n.next()
                    show_image_chat(n, data["sender"]["id"])
            elif msg.startswith("speed"):
                start_time = 1509739849 # !!
                query = {"user_name": self.user, "summary":{"$exists": True}, "time": {"$gt": start_time, "$lt": time.time()}}
                cams = db.mongo.images.find(query).distinct("cam_id")

                for cam in cams:
                    msg = []
                    
                    query = {"user_name": self.user, "cam_id":cam, "pose":{"$exists": True}, "detections":{"$exists": True}, "time": {"$gt": start_time, "$lt": time.time()}}
                    t = db.mongo.images.find(query).limit(1).sort([("time", -1)])[0]["time"]
                    msg.append("{}: last processed image: {:.2f} ({:.2f} secs ago)".format(cam, t, time.time()-t))
                    
                    query = {"user_name": self.user, "cam_id":cam, "time": {"$gt": time.time()-60, "$lt": time.time()}}
                    cnt = db.mongo.images.find(query).count()
                    msg.append("{}: images received in last minute: {}".format(cam, cnt))
                    
                    query = {"user_name": self.user, "cam_id":cam, "pose":{"$exists": True}, "detections":{"$exists": True},"time": {"$gt": time.time()-60, "$lt": time.time()}}
                    cnt = db.mongo.images.find(query).count()
                    msg.append("{}: images processed in last minute: {}".format(cam, cnt))
                    
                    query = {"user_name": self.user, "cam_id":cam, "pose":{"$exists": True}, "detections":{"$exists": True}, "time": {"$gt": time.time()-3600, "$lt": time.time()}}
                    hr_cnt = db.mongo.images.find(query).count()
                    msg.append("{}: image processed in last hour: {} ({:.2f}/min)".format(cam, hr_cnt, hr_cnt/60))
                    
                    msg.append("---")
                
                    chatbot.send_fb_message(sender, "\n".join(msg))
                    

    def execute(self):
        return []
