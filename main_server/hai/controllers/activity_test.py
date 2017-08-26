from .controller import Controller
import database as db
import cv2
import colorsys
from server_actors import chatbot
from threading import Timer
import os
import time
import utils

class ActivityTest(Controller):
    def __init__(self, user):
        self.user = user

    def on_event(self, event, data):
        if event == "chat":
            msg = data["message"]["text"]

            if msg == "activity?":
              n = db.mongo.images.find({"user_name": self.user, "summary":{"$exists": True}}).sort([("time",-1)]).limit(1).next()
              summ = n["summary"]
              
              for det in summ:
                if det["label"] == "person":
                  if "keypoints" in det:
                    left_pts = utils.get_avg_pt(det["keypoints"]["hand_left_keypoints"])
                    right_pts = utils.get_avg_pt(det["keypoints"]["hand_right_keypoints"])

                    if left_pts != None:
                      chatbot.send_fb_message(data["sender"]["id"], "left " + str(left_pts))
                    if right_pts != None:
                      chatbot.send_fb_message(data["sender"]["id"], "right " + str(right_pts))

    def execute(self):
        return []
