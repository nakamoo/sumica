from .controller import Controller

class Learner(Controller):
    def __init__(self):
        pass

    def on_event(self, event, data):
        if event == "timer":
            n = db.mongo.images.find({"user_name": self.user, "keypoints":{"$exists": True},
              "detections":{"$exists": True}}).sort([("time",-1)]).limit(1)
            if n.count() <= 0:
                return
            n = n.next()
            pose = n["keypoints"]
            path = n["filename"]
            dets = n["detections"]["objects"]

            summary = summarize(path, dets, pose)
            db.mongo.images.update_one({"_id": n["_id"]}, {'$set': {'summary': summary}}, upsert=False)
            db.trigger_controllers(self.user, "summary", {"_id": n["_id"], "summary": summary})

    def execute(self):
        return []