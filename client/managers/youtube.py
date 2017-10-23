import time
import subprocess
from subprocess import Popen

class Manager:
    def __init__(self, user, server_ip, actions):
        self.now_playing = None

    def start(self):
        pass

    def execute(self, acts):
        for act in acts:
            if act["platform"] == "play_youtube":
                try:
                    Popen("mpsyt /{}, 1".format(act['data']), shell=True)
                    self.now_playing = act['data']
                except:
                    pass

            if act["platform"] == "stop_youtube":
                try:
                    Popen('pkill -f mpsyt', shell=True)
                    Popen('pkill -f omxplayer', shell=True)
                    self.now_playing = None
                except:
                    pass

if __name__ == "__main__":
    youtubeplayer = Manager('sample', '1.0.0.0')
    # youtubeplayer.execute([{'platform': 'play_youtube', 'data': 'nujages'}])
    youtubeplayer.execute([{'platform': 'stop_youtube', 'data': ''}])
