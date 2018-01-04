from controllers.learner.i3dnn import I3DNN
from .controller import Controller
from controllers.utils import filter_persons
from _app import app
import cv2
import numpy as np
import database as db
import time

class ActionRecognition(Controller):
    def __init__(self):
        self.nn = I3DNN()

    def on_event(self, event, data):
        if event == "image":
            if app.config['ENCRYPTION']:
                image_path = app.config['ENCRYPTED_IMG_DIR'] + data['filename']
            else:
                image_path = app.config['RAW_IMG_DIR'] + data['filename']

            n = db.mongo.images.find_one({"_id": data["_id"]})
            persons, pose_indices = filter_persons(n)
            
            img = cv2.imread(image_path)
            whole_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) / 128.0 - 1.0
            updates = {"history.action_request": time.time()}
            
            for i in range(len(n["detections"])):
                if n["detections"][i]["label"] == "person":
                    updates["detections.{}.passed".format(i)] = i in persons
                    if i in persons:
                        box = n["detections"][i]["box"]
                        longer_side = max(box[2]-box[0],box[3]-box[1])
                        longer_side = min(min(whole_img.shape[1], longer_side), whole_img.shape[0])
                            
                        a = longer_side//2
                        cx, cy = (box[0]+box[2])//2, (box[1]+box[3])//2
                        x1, y1, x2, y2 = cx-a, cy-a, cx+a, cy+a
                        if x1 < 0:
                            x2 -= x1
                            x1 = 0
                        if y1 < 0:
                            y2 -= y1
                            y1 = 0
                        if x2 >= whole_img.shape[1]:
                            x1 -= x2-whole_img.shape[1]
                            x2 = whole_img.shape[1]
                        if y2 >= whole_img.shape[0]:
                            y1 -= y2-whole_img.shape[0]
                            y2 = whole_img.shape[0]
                            
                        crop = whole_img[y1:y2,x1:x2,:]
                        crop = cv2.resize(crop, (224, 224))
                        img = np.array([[crop for _ in range(10)]])
                        prob, logits, label, feats = self.nn.process_image(img)
                        updates["detections.{}.action".format(i)] = label
                        updates["detections.{}.action_confidence".format(i)] = float(prob)
                        updates["detections.{}.action_crop".format(i)] = [x1,y1,x2,y2]
                        updates["detections.{}.action_vector".format(i)] = feats
                        
                        a = persons.index(i)
                        if pose_indices[a] is not None:
                            updates["detections.{}.pose_body_index".format(i)] = pose_indices[a]

            updates["history.action_recorded"] = time.time()
            db.mongo.images.update_one({"_id": data["_id"]}, {'$set': updates}, upsert=False)

    def execute(self):
        return []