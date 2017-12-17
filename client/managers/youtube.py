import time
import subprocess
from subprocess import Popen
import requests
from bs4 import BeautifulSoup

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
                    try:
                        youtube_result = Youtube(act['data'], result=1)
                        Popen("mpv '" + youtube_result.url[0] + "' --loop --no-video > /dev/null 2>&1", shell=True)
                    except:
                        Popen("mpv https://www.youtube.com/watch?v=HKKe7p44PDY --loop --no-video > /dev/null 2>&1", shell=True)
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
        self.title = [h3.a.get("title") for h3 in h3s]
        self.id = [h3.a.get("href").split("=")[-1] for h3 in h3s]
        self.embed = ["https://www.youtube.com/embed/" + h3.a.get("href").split("=")[-1] for h3 in h3s]
        self.time = [h3.span.text.replace(" - 長さ: ","").replace("。","") for h3 in h3s]
        self.info = [h3.text for h3 in h3s] # >>タイトル　- 長さ：00:00。

    def select(self):
        values = {"url":self.url,"title":self.title,"id":self.id,"embed":self.embed,"time":self.time}
        info = self.info
        for i in range(len(info)):
            print("%s:%s" % (i,info[i]))
        while True:
            try:
                num = int(input("番号:"))
                break
            except:
                print("番号を正しく入力してください。")
        results = {
            "url":values["url"][num],
            "title":values["title"][num],
            "id":values["id"][num],
            "embed":values["embed"][num],
            "time":values["time"][num],
            }
        return results

if __name__ == "__main__":
    youtubeplayer = Manager('sample', '1.0.0.0', None)
    youtubeplayer.execute([{'platform': 'play_youtube', 'data': 'n'}])
    # youtubeplayer.execute([{'platform': 'stop_youtube', 'data': ''}])
