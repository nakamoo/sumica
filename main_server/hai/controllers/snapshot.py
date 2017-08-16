from .controller import Controller

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
        n = db.mongo.detections.find({"user_name": self.user}).sort([("time",-1)]).limit(1)
        dets = n["detections"]["objects"]
        path = n["path"]

        n = db.mongo.pose.find_one({"path": path})
        pose = n["keypoints"]

        img = draw(path, dets, pose)
        pass

    def execute(self):
        return []
