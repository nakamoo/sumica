from .controller import Controller
import database as db
import cv2
import colorsys
from server_actors import chatbot
from threading import Timer
import os
import time
import controllers.utils as utils

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
                  if "keypoints" in det and det["keypoints"] is not None:
                    left_pts = utils.get_avg_pt(det["keypoints"]["hand_left_keypoints"])
                    right_pts = utils.get_avg_pt(det["keypoints"]["hand_right_keypoints"])

                    if left_pts != None:
                      chatbot.send_fb_message(data["sender"]["id"], "left h" + str(left_pts))
                    if right_pts != None:
                      chatbot.send_fb_message(data["sender"]["id"], "right h" + str(right_pts))

                    def get_body_part(name):  
                      part = list(utils.chunker(pose_pts, 3))[utils.keypoint_labels.index(name)]
                      part = list(part)[:2] if part[2] >= 0.05 else None
                      return part

                    pose_pts = det["keypoints"]["pose_keypoints"]
                    left_wrist = get_body_part("LWrist")
                    right_wrist = get_body_part("RWrist")

                    if left_wrist != None:
                      chatbot.send_fb_message(data["sender"]["id"], "left w" + str(left_wrist))
                    if right_wrist != None:
                      chatbot.send_fb_message(data["sender"]["id"], "right w" + str(right_wrist))

                    touch_pts = [left_wrist, right_wrist, left_pts, right_pts]

                    def check_touch(pt):
                      if pt is None:
                        return

                      for det2 in summ:
                        if det2 != det and det2["label"] != "bed":
                          box = det2["box"]
                          if pt[0] > box[0]-50 and pt[0] < box[2]+50 and pt[1] > box[1]-50 and pt[1] < box[3]+50:
                            chatbot.send_fb_message(data["sender"]["id"], "touching " + det2["label"]) 

                    for pt in touch_pts:
                      check_touch(pt)

                    left_ear = get_body_part("LEar")
                    right_ear = get_body_part("REar")
                    nose = get_body_part("Nose")

                    if nose is not None:
                      if left_ear is not None and right_ear is not None:
                        origin = [(left_ear[0] + right_ear[0]) / 2.0, (left_ear[1] + right_ear[1]) / 2.0]
                      elif left_ear is not None:
                        origin = left_ear
                      elif right_ear is not None:
                        origin = right_ear
                      else:
                        origin = None

                    def check_look(pt):
                      for det2 in summ:
                        if det2 != det and det2["label"] != "bed" and det2["label"] != "chair":
                          box = det2["box"]
                          if pt[0] > box[0] and pt[0] < box[2] and pt[1] > box[1] and pt[1] < box[3]:
                            chatbot.send_fb_message(data["sender"]["id"], "looking at " + det2["label"])
                            return True
                      return False
   
                    if origin is not None:
                          chatbot.send_fb_message(data["sender"]["id"], "looking from {} to {}".format(str(origin), str(nose)))
                          step = [nose[0] - origin[0], nose[1] - origin[1]]
                          for dist in range(0, 100):
                            pt = [nose[0] + step[0] * dist, nose[1] + step[1] * dist]
                            done = check_look(pt)
                            if done:
                              break
                            

    def execute(self):
        return []
