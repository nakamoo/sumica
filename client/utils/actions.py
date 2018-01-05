from subprocess import Popen
import subprocess
import json
import time

from utils.irkit import IrkitInternetAPI
from utils.speechrecognition import confirm
irkit = IrkitInternetAPI()

import utils.tts as tts

class Actions:
    def __init__(self):
        self.last_hue_update = {"data": None}
        self.hue_overridden = False

    def act_list(self, actions):
        for action in actions:
            if "platform" in action and "data" in action:
                if "confirmation" in action:
                    self.act(action["platform"], action["data"],
                            confirmation=action['confirmation'])
                else:
                    self.act(action["platform"], action["data"])

    def act(self, platform, data, confirmation=None):
        print(">>", platform)
        if platform == "youtube":
            print("OPENING YOUTUBE")
            Popen("node utils/youtube.js {}".format(data), shell=True)
        elif platform == "shell":
            Popen("{}".format(data), shell=True)
        elif platform == "print":
            print(data)
        elif platform == "sound":
            Popen("play ../sounds/{}".format(data), shell=True)
        elif platform == "hue":
            json_data = json.loads(data)

            #if self.last_hue_update["data"] != json_data:
            with open('utils/hue_state.json', 'w+') as outfile:
                json.dump(json_data, outfile)

            print("setting hue", data)
            out = subprocess.check_output(['node', 'utils/hue.js', 'set_state'])
            print(out.decode('utf-8'))
            self.last_hue_update = {"data":json_data, "time":time.time()}
            self.hue_overridden = False
        elif platform == "irkit":
            if confirmation is not None:
                tts.say(confirmation)
                ans = confirm()
                if ans is None:
                    tts.say("上手く聞こえませんでした")
                    return
                elif not ans:
                    tts.say("わかりました，操作をキャンセルします")
                    return
                irkit.post_messages(data)
            else:
                irkit.post_messages(data)

        elif platform == "tts":
                tts.say(data)
