from .controller import Controller
import database as db
import cv2
import colorsys
from server_actors import chatbot
from threading import Timer
import os

def overlap(box, pts):
    for x, y in pts:
      if x > box[0] and x < box[2] and y > box[1] and y < box[2]:
        return True

    return False

def visualize(frame, dets, pts):
    for result in dets:
        det = result["box"]
 
        if result["label"] == "person":
           if result["confidence"] > 0.7 or overlap(det, pts):
              pass
           else:
              continue

        name = result["label"] + ": " + "%.2f" % result["confidence"]

        i = sum([ord(x) for x in name])
        c = colorsys.hsv_to_rgb(i%100.0/100.0, 1.0, 0.9)
        c = tuple([int(x * 255.0) for x in c])
        cv2.putText(frame, name, (det[0], det[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, c, 2)
        cv2.rectangle(frame, (det[0], det[1]), (int(det[2]), int(det[3])), c, 2)

    return frame

def chunker(seq, size):
  print(seq)
  return (seq[pos:pos+size] for pos in range(0, len(seq), size))

def to_list(pose):
    pts = []
    for person in pose["people"]:
      def get_points(pts):
        for x, y, c in chunker(pts, 3):
          #print(x, y, c)
          #print(type(c))
          if c > 0.05:
            pts.append([int(x), int(y)])

      get_points(person["pose_keypoints"])
      get_points(person["hand_left_keypoints"])
      get_points(person["hand_right_keypoints"])
    return pts

def draw(path, dets, pose):
    #print(path)
    #print(dets)
    #print(pose)

    import hai

    print(os.path.join(hai.app.config["RAW_IMG_DIR"], path))

    img = cv2.imread(hai.app.config["RAW_IMG_DIR"] + path)
    img = visualize(img, dets, to_list(pose))

    for person in pose["people"]:
      print(person)
      def draw_points(pts):
        try:
          for x, y, c in chunker(pts, 3):
            #print(x, y, c)
            if c > 0.05:
              cv2.circle(img, (int(x), int(y)), 3, (0, 255, 0), -1)
        except:
          pass

      draw_points(person["pose_keypoints"])
      draw_points(person["hand_left_keypoints"])
      draw_points(person["hand_right_keypoints"])

    return img

class Snapshot(Controller):
    def __init__(self, user):
        self.user = user

    def on_event(self, event, data):
        if event == "chat":
            msg = data["message"]["text"]

            if msg == "snapshot":
              n = db.mongo.pose.find({"user_name": self.user}).sort([("time",-1)]).limit(1).next()
              pose = n["keypoints"]
              fn = n["filename"]
              n = db.mongo.detections.find_one({"user_name": self.user, "filename": fn})
              dets = n["detections"]["objects"]
              path = n["filename"]
         
              img = draw(path, dets, pose)
              #print("sending: ", "http://153.120.159.210:5000/static/" + path)
              #img = cv2.resize(img, (0,0), fx=0.5, fy=0.5)
              #print(img)
              import hai

              print("writing to: ", path)
              cv2.imwrite("./static/" + path, img)
              chatbot.send_fb_message(data["sender"]["id"], "here's your image")
              url = "http://homeai.ml:{}/static/".format(hai.port) + path
              print("snapshot url:", url)
              chatbot.send_fb_image(data["sender"]["id"], url)
             
              #os.remove("./static/" + path)
              def rem(path):
                os.remove(path)
              Timer(30.0, rem, ("./static/" + path,)).start()


    def execute(self):
        return []
