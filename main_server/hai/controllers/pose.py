from .controller import Controller
import subprocess
from shutil import copyfile
from subprocess import check_output
import glob
import time
import os
import threading
import json
import database as db
import time
from _app import app

import coloredlogs, logging
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', logger=logger)

for f in glob.glob("./pose_data/*"):
    os.remove(f)

def manage_data():
    json_files = glob.glob("./pose_data/*")
    logger.debug(str(len(json_files)) + " pose files")
    
    for f in json_files:
        try:
            # print(open(f, "r").readlinesi())
            pts = json.load(open(f, "r"))
            name = f[:-15].split("/")[-1] + ".png"
            pose_data = {"keypoints": pts}
            #image_info = db.mongo.images.find_one({"filename": name})
            #pose_data.update(image_info)
            #db.mongo.pose.insert_one(pose_data)

            n = db.mongo.images.update_one({"filename": name}, {'$set': {'keypoints': pts, "history.pose_recorded": time.time()}}, upsert=False)
            #print("POSE:", pose_done, pose_done-image_info["history"]["first_loop_done"])
            os.remove(f)
        except Exception as e:
            #pass
            logger.warning("missing file", f, e)
            os.remove(f)
    #time.sleep(0.1)
    

class Pose(Controller):
    def __init__(self):
        pass

    def on_event(self, event, data):
        if event == "image":
            if app.config['ENCRYPTION']:
                image_path = app.config['ENCRYPTED_IMG_DIR'] + data['filename']
            else:
                image_path = app.config['RAW_IMG_DIR'] + data['filename']

            new_data = {}
            new_data['history.pose_request'] = time.time()
            copyfile(image_path, './pose_tmp/' + data['filename'])
            
            db.mongo.images.update_one({"_id": data["_id"]}, {'$set': new_data}, upsert=False)
            #time.sleep(1)
            #manage_data()

        elif event == "timer":
            manage_data()

    def execute(self):
        return []
