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

for f in glob.glob("./pose_data/*"):
    os.remove(f)

def subprocess_cmd(command):
    proc = subprocess.Popen([command],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, shell=True)
    stdout, stderr = proc.communicate()
    #out = check_output([command])
    #proc_stdout = process.communicate()
    print(stdout, stderr)

def manage_data():
    json_files = glob.glob("./pose_data/*")
    for f in json_files:
                try:
                  #print(open(f, "r").readlinesi())
                  pts = json.load(open(f, "r"))
                  name = f[:-15].split("/")[-1] + ".png"
                  pose_data = {"keypoints": pts}
                  image_info = db.mongo.images.find_one({"filename": name})
                  pose_data.update(image_info)
                  #db.mongo.pose.insert_one(pose_data)

                  db.mongo.images.update_one({"filename": name}, {'$set': {'keypoints': pts}}, upsert=False)
                  os.remove(f)
                except Exception as e:
                  #pass
                  print("missing file", f)
    #time.sleep(0.1)

def update_loop():
    while True:
        """
        files = glob.glob("./pose_tmp/*")
        if len(files) > 0:
            print("executing subprocess")
            subprocess_cmd('cd ~/openpose; ./build/examples/openpose/openpose.bin --no_display --image_dir ~/HAI/main_server/hai/pose_tmp --write_keypoint_json ~/HAI/main_server/hai/pose_data --num_gpu 2 --num_gpu_start 1 --face --hand')
            print("clearing pose_tmp")
            for f in files:
                os.remove(f)
         """
        manage_data()
        #else:
        #    time.sleep(1)

#if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
#print("starting pose estimation thread...")
#thread_stream = threading.Thread(target=update_loop)
#thread_stream.daemon = True
#thread_stream.start()

#print("starting pose estimation subprocess...")
#subprocess.call(['cd ~/openpose; ./build/examples/user_code/mytest.bin --image_dir ~/HAI/main_server/hai/pose_tmp --write_keypoint_json ~/HAI/main_server/hai/pose_data --num_gpu 2 --num_gpu_start 1 --face --hand'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

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
