from .controller import Controller
import database as db
import cv2
import colorsys
from server_actors import chatbot
from threading import Timer
import os
import time
import controllers.utils as utils
import json
import numpy as np

def extract_features(summary):
    for obj in summary:
                if obj["label"] == "person":
                  looked_obj = None
                  touched_obj = []
                    
                  if "keypoints" in obj and obj["keypoints"] is not None:
                    # get objects touched by hand
                    pose_pts = obj["keypoints"]["pose_keypoints"]

                    def get_body_part(name):  
                      part = list(utils.chunker(pose_pts, 3))[utils.keypoint_labels.index(name)]
                      part = list(part)[:2] if part[2] >= 0.05 else None
                      return part
                
                    def get_hand_pts(data):
                        pts = []
                        for x, y, c in list(utils.chunker(data, 3)):
                            if c >= 0.05:
                                pts.append([x, y])
                        return pts
                
                    left_hand_pts = get_hand_pts(obj["keypoints"]["hand_left_keypoints"])
                    right_hand_pts = get_hand_pts(obj["keypoints"]["hand_right_keypoints"])
                    
                    left_wrist = get_body_part("LWrist")
                    right_wrist = get_body_part("RWrist")

                    #if left_wrist != None:
                    #  chatbot.send_fb_message(data["sender"]["id"], "left w" + str(left_wrist))
                    #if right_wrist != None:
                    #  chatbot.send_fb_message(data["sender"]["id"], "right w" + str(right_wrist))

                    touch_pts = [left_wrist, right_wrist] + left_hand_pts + right_hand_pts

                    def check_touch(pt):
                      touched_objects = []
                    
                      if pt is None:
                        return touched_objects
                      
                      for obj2 in summary:
                        if obj2 != obj and obj2["label"] != "bed":
                          box = obj2["box"]
                          if pt[0] > box[0] and pt[0] < box[2] and pt[1] > box[1] and pt[1] < box[3]:
                            touched_objects.append(obj2["label"])
                      return touched_objects

                    
                    for pt in touch_pts:
                      touched_obj.extend(check_touch(pt))

                    # get objects being looked at
                    left_ear = get_body_part("LEar")
                    right_ear = get_body_part("REar")
                    nose = get_body_part("Nose")

                    origin = None
                    if nose is not None:
                      if left_ear is not None and right_ear is not None:
                        origin = [(left_ear[0] + right_ear[0]) / 2.0, (left_ear[1] + right_ear[1]) / 2.0]
                      elif left_ear is not None:
                        origin = left_ear
                      elif right_ear is not None:
                        origin = right_ear
                        

                    def check_look(pt):
                      for obj2 in summary:
                        if obj2 != obj and obj2["label"] != "bed" and obj2["label"] != "chair":
                          box = obj2["box"]
                          if pt[0] > box[0] and pt[0] < box[2] and pt[1] > box[1] and pt[1] < box[3]:
                            #chatbot.send_fb_message(data["sender"]["id"], "looking at " + obj2["label"])
                            return obj2["label"]
                      return None
   
                    
                    if origin is not None:
                          #chatbot.send_fb_message(data["sender"]["id"], "looking from {} to {}".format(str(origin), str(nose)))
                          step = [nose[0] - origin[0], nose[1] - origin[1]]
                          for dist in range(0, 100):
                            pt = [nose[0] + step[0] * dist, nose[1] + step[1] * dist]
                            looked_obj = check_look(pt)
                            if looked_obj is not None:
                              break
                            
                    #return set(touched_obj), looked_obj
                  obj["touching"] = list(set(touched_obj))
                  obj["looking"] = str(looked_obj)
                  

class ActivityTest(Controller):
    def __init__(self, user):
        self.user = user
        self.re = []
        self.history = []
        self.msg = ""
        
    def control_hue(self, summary):
        hue = 10000
        bri = 255
        msg = "NONE"
        vec = [0, 0, 0, 0, 0]
        act_id = 0
        alpha = 1

        for obj in summary:
            if obj["label"] == "person":
                act_id = 1

                if "laptop" in obj["touching"]:
                    print("laptop")
                    act_id = 2
                    #alpha = 2
                    break
                elif  "book" in obj["touching"]:
                    print("book")
                    act_id = 3
                    #alpha = 2
                    break
                elif "cell phone" in obj["touching"]:
                    print("phone")
                    act_id = 4
                    #alpha = 2
                    break
                else:
                    print("just person")
                    
        labels = ["no person", "person", "laptop", "book", "phone"]
        vec[act_id] = alpha
    
        self.history.append(vec)
        
        if len(self.history) >= 2:
            data = self.history[-2:]
            
            weights = np.mean(data, axis=0)
            decision = np.argmax(weights)
            print(labels[decision], [label + ": " + str(weight) for label, weight in zip(labels, weights)])

            if decision == 0:
                bri = 100
                hue = 10000
            elif decision == 1:
                bri = 255
            elif decision == 2 or decision == 4:
                bri = 255
                hue = 20000
            elif decision == 3:
                bri = 255
                hue = 50000
        
        self.re =  [{"platform": "hue", "data": json.dumps({"on": True, "hue":hue, "brightness":bri})}]

    def on_event(self, event, data):
        if event == "chat":
            msg = data["message"]["text"]

            if msg == "activity?":
              n = db.mongo.images.find({"user_name": self.user, "summary":{"$exists": True}}).sort([("time",-1)]).limit(1).next()
              summ = n["summary"]
              
              #touched_obj, looked_obj = extract_features()
              #print(touched_obj, looked_obj)
        elif event == "summary":
            summ = data["summary"]
            extract_features(summ)
            db.mongo.images.update_one({"_id": data["_id"]}, {'$set': {'summary': summ}}, upsert=False)
            
            #self.control_hue(summ)

    def execute(self):
        re = self.re
        self.re = []
        return re
