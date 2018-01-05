import time
import subprocess
from subprocess import Popen
import requests
from bs4 import BeautifulSoup

import sys, os
pardir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(pardir)
import utils.tts as tts
from utils.speechrecognition import confirm
import traceback

class Manager:
    def __init__(self, user, server_ip, actions):
        self.now_playing = None

    def start(self):
        pass

    def execute(self, acts):
        for act in acts:
            if act["platform"] == "play_youtube":
                if "confirmation" in act:
                    tts.say(act['confirmation'])
                    time.sleep(0.5)
                    ans = confirm()
                    if ans is None:
                        tts.say("上手く聞こえませんでした")
                        return
                    elif not ans:
                        tts.say("わかりました，再生をキャンセルします")
                        return

                try:
                    Popen('pkill -9 mpv', shell=True)
                    time.sleep(0.3)
                    tts.say(act['data'] + "を検索します")
                    try:
                        youtube_result = Youtube(act['data'], result=1)
                        Popen("mpv '" + youtube_result.url[0] + "' --loop --no-video > /dev/null 2>&1", shell=True)
                    except:
                        tts.say(act['data'] + "は見つかりませんでした")
                        # Popen("mpv https://www.youtube.com/watch?v=HKKe7p44PDY --loop --no-video > /dev/null 2>&1", shell=True)
                    self.now_playing = act['data']
                except:
                    traceback.print_exc()

            if act["platform"] == "stop_youtube":
                try:
                    Popen('pkill -9 mpv', shell=True)
                    self.now_playing = None
                except:
                    traceback.print_exc()

class Youtube():
    def __init__(self,query,result=10): # max20まで
        search_url = "https://www.youtube.com/results?search_query=" + query
        req = requests.get(search_url)
        soup = BeautifulSoup(req.text.encode(req.encoding).decode('utf-8','strict'), "html.parser")
        h3s = soup.find_all("h3", {"class":"yt-lockup-title"})[0:result+1]

        self.data = [h3 for h3 in h3s]
        self.url = ["https://www.youtube.com" + h3.a.get('href') for h3 in h3s]

if __name__ == "__main__":
    # youtubeplayer = Manager('sample', '1.0.0.0', None)
    # youtubeplayer.execute([{'platform': 'play_youtube', 'data': 'n'}])
    # youtubeplayer.execute([{'platform': 'stop_youtube', 'data': ''}])
    yt = Youtube('nujabes')
