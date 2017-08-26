from .controller import Controller
import database as db
import cv2
import colorsys
from server_actors import chatbot
from threading import Timer
import os
import time

def chunker(seq, size):
  return (seq[pos:pos+size] for pos in range(0, len(seq), size))

def overlap(box, poses):
  for person in poses["people"]:
    all_pts = []

    def get_points(pts):
      for x, y, c in chunker(pts, 3):
        if c > 0.05:
          all_pts.append([int(x), int(y)])

    get_points(person["pose_keypoints"])
    get_points(person["hand_left_keypoints"])
    get_points(person["hand_right_keypoints"])

    for x, y in all_pts:
      if x > box[0] and x < box[2] and y > box[1] and y < box[2]:
        poses["people"].remove(person)
        return person, poses

    return None, poses

def filter(path, dets, poses):
  beds = []
  for result in dets:
      if result["label"] == "bed":
         beds.append((result, result["confidence"]))

  beds = sorted(beds, key=lambda tup: tup[1], reverse=True)
  max_beds = 1 # assumption
  if len(beds) > max_beds:
      for b, conf in beds[max_beds:]:
          dets.remove(b)

  summary = []

  for result in dets:
      box = result["box"]

      if result["label"] == "person":
         match, poses = overlap(box, poses)
 
         if result["confidence"] > 0.7 or match is not None:
            result["keypoints"] = match
            summary.append(result)
         else:
            continue
      else:
        summary.append(result)
  
  return summary

class Summarizer(Controller):
    def __init__(self, user):
        self.user = user

    def on_event(self, event, data):
        if event == "image":
            n = db.mongo.images.find({"user_name": self.user, "keypoints":{"$exists": True},
              "detections":{"$exists": True}}).sort([("time",-1)]).limit(1).next()
            pose = n["keypoints"]
            path = n["filename"]
            dets = n["detections"]["objects"]

            summary = filter(path, dets, pose)
            db.mongo.images.update_one({"_id": n["_id"]}, {'$set': {'summary': summary}}, upsert=False)

    def execute(self):
        return []
