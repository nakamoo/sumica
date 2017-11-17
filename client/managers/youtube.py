import time
import subprocess
from subprocess import Popen
import traceback

class Manager:
    def __init__(self, user, server_ip, actions):
        self.now_playing = None

    def start(self):
        pass

    def execute(self, acts):
        for act in acts:
            if act["platform"] == "play_youtube":
                try:
                    Popen('pkill -9 mpv', shell=True)
                    time.sleep(0.3)
                    if act['data'] == 'j':
                        Popen("mpv 'https://www.youtube.com/watch?v=3jWRrafhO7M' --no-video > /dev/null 2>&1", shell=True)
                    elif act['data'] == 'n':
                        Popen("mpv 'https://www.youtube.com/watch?v=WrO9PTpuSSs' --no-video > /dev/null 2>&1", shell=True)
                    self.now_playing = act['data']
                except:
                    traceback.print_exc()

            if act["platform"] == "stop_youtube":
                try:
                    Popen('pkill -9 mpv', shell=True)
                    self.now_playing = None
                except:
                    traceback.print_exc()

if __name__ == "__main__":
    youtubeplayer = Manager('sample', '1.0.0.0', None)
    youtubeplayer.execute([{'platform': 'play_youtube', 'data': 'n'}])
    # youtubeplayer.execute([{'platform': 'stop_youtube', 'data': ''}])
