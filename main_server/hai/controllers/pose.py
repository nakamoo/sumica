from .controller import Controller
import subprocess
from shutil import copyfile

def subprocess_cmd(command):
    process = subprocess.Popen(command,stdout=subprocess.PIPE, shell=True)
    proc_stdout = process.communicate()[0].strip()
    print proc_stdout

class Pose(Controller):
    def __init__(self):
        pass

    def on_event(self, event, data):
        if event == "image":
            image_path = './images/' + data['filename']
            copyfile(image_path, './pose_tmp/' + data['filename'])
            subprocess_cmd('cd ~/openpose; ./openpose/build/examples/openpose/openpose.bin --no_display --image_dir ~/HAI/main_server/hai/pose_tmp --write_images outs --num_gpu 2 --num_gpu_start 2')
            for f in glob.glob("./pose_tmp/*"):
                os.remove(f)

    def execute(self):
        return []
