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

for f in glob.glob("./pose_data/*"):
    os.remove(f)


def subprocess_cmd(command):
    proc = subprocess.Popen([command],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, shell=True)
    stdout, stderr = proc.communicate()
    # out = check_output([command])
    # proc_stdout = process.communicate()
    print(stdout, stderr)


def manage_data():
    json_files = glob.glob("./pose_data/*")
    for f in json_files:
        try:
            # print(open(f, "r").readlinesi())
            pts = json.load(open(f, "r"))
            name = f[:-15].split("/")[-1] + ".png"
            pose_data = {"keypoints": pts}
            image_info = db.mongo.images.find_one({"filename": name})
            #pose_data.update(image_info)
            #db.mongo.pose.insert_one(pose_data)

            pose_done = time.time()
            n = db.mongo.images.update_one({"filename": name}, {'$set': {'keypoints': pts, "history.second_loop_done": pose_done}}, upsert=False)
            #print("POSE:", pose_done, pose_done-image_info["history"]["first_loop_done"])
            os.remove(f)
        except Exception as e:
            #pass
            print("missing file", f, e)
            os.remove(f)
    #time.sleep(0.1)

class Pose(Controller):
    def __init__(self):
        pass

    def on_event(self, event, data):
        if event == "image":
            from _app import app
            if app.config['ENCRYPTION']:
                image_path = app.config['ENCRYPTED_IMG_DIR'] + data['filename']
            else:
                image_path = app.config['RAW_IMG_DIR'] + data['filename']
            print("copying to pose_tmp")
            copyfile(image_path, './pose_tmp/' + data['filename'])
        elif event == "timer":
            manage_data()

    def execute(self):
        return []
