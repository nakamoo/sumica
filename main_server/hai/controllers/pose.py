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

def subprocess_cmd(command):
    proc = subprocess.Popen([command],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, shell=True)
    stdout, stderr = proc.communicate()
    #out = check_output([command])
    #proc_stdout = process.communicate()
    print(stdout, stderr)

def update_loop():
    while True:
        files = glob.glob("./pose_tmp/*")
        if len(files) > 0:
            print("executing subprocess")
            subprocess_cmd('cd ~/openpose; ./build/examples/openpose/openpose.bin --no_display --image_dir ~/HAI/main_server/hai/pose_tmp --write_keypoint_json ~/HAI/main_server/hai/pose_data --num_gpu 1 --num_gpu_start 1 --face --hand')
            print("clearing pose_tmp")
            for f in files:
                os.remove(f)

            json_files = glob.glob("./pose_data/*")
            for f in json_files:
                try:
                  pts = json.load(open(f, "r"))
                  #print(f)
                  name = f[:-15].split("/")[-1] + ".png"
                  #print(name)
                  data = {"keypoints": pts}
                  image_info = db.mongo.images.find_one({"filename": name})
                  data.update(image_info)
                  db.mongo.pose.insert_one(data)
                except Exception as e:
                  print(e)
                os.remove(f)
        else:
            time.sleep(1)

if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    print("starting pose estimation thread...")
    thread_stream = threading.Thread(target=update_loop)
    thread_stream.daemon = True
    thread_stream.start()

class Pose(Controller):
    def __init__(self):
        pass

    def on_event(self, event, data):
        if event == "image":
            import hai
            image_path = os.path.join(hai.app.config["RAW_IMG_DIR"], data['filename'])
            copyfile(image_path, './pose_tmp/' + data['filename'])

    def execute(self):
        return []
