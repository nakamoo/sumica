from .controller import Controller
import cv2

def visualize(frame, dets):
    for result in dets:
        det = result["box"]
        name = result["label"]

        i = sum([ord(x) for x in name])
        c = colorsys.hsv_to_rgb(i%100.0/100.0, 1.0, 0.9)
        c = tuple([int(x * 255.0) for x in c])
        cv2.putText(frame, name, (det[0], det[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, c, 2)
        cv2.rectangle(frame, (det[0], det[1]), (int(det[2]), int(det[3])), c, 2)

    return frame

def draw(path, dets, pose):
    #print(path)
    #print(dets)
    #print(pose)

    img = cv2.imread("./images/" + path)
    img = visualize(img, dets)

    return img

class Snapshot(Controller):
    def __init__(self, user):
        self.user = user

    def on_event(self, event, data):
        #if event == "chat":
            #msg = data["message"]["text"]

            #if msg == "snapshot":
        n = db.mongo.detections.find({"user_name": self.user}).sort([("time",-1)]).limit(1)
        dets = n["detections"]["objects"]
        path = n["path"]

        n = db.mongo.pose.find_one({"path": path})
        pose = n["keypoints"]

        img = draw(path, dets, pose)
        print(img.size)

    def execute(self):
        return []
