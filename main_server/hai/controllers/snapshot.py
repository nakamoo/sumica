from .controller import Controller
import database as db

def draw(path, dets, pose):
    print(path)
    print(dets)
    print(pose)
    pass

class Snapshot(Controller):
    def __init__(self, user):
        self.user = user

    def on_event(self, event, data):
        #if event == "chat":
            #msg = data["message"]["text"]

            #if msg == "snapshot":
        n = db.mongo.pose.find({"user_name": self.user}).sort([("time",-1)]).limit(1).next()
        pose = n["keypoints"]
        fn = n["filename"]
        n = db.mongo.detections.find_one({"filename": fn})
        dets = n["detections"]["objects"]
        path = n["filename"]
         
        img = draw(path, dets, pose)
        pass

    def execute(self):
        return []
