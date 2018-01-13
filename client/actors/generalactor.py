from subprocess import Popen
import subprocess
import json
import time
import requests
import logging

from utils.irkit import IrkitInternetAPI
from utils.speechrecognition import confirm
irkit = IrkitInternetAPI()

from actors.actor import Actor
import utils.tts as tts

class GeneralActor(Actor):
    def __init__(self, user, server_ip):
        self.user = user
        self.ip = server_ip

    def execute(self, acts):
        for action in acts:
            if "platform" in action and "data" in action:
                if "confirmation" in action:
                    self.act(action["platform"], action["data"],
                            confirmation=action['confirmation'])
                else:
                    self.act(action["platform"], action["data"])

    def act(self, platform, data, confirmation=None):
        print(">>", platform)
        if platform == "irkit":
            if confirmation is not None:
                ans = confirm(confirmation)
                data_confirm = {'platform': platform, 'data': data, 'user_name': self.user,
                        'confirmation': confirmation, 'answer': ans}
                r = requests.post("%s/data/confirmation" % self.ip, data=data_confirm, verify=False, timeout=1)
                logging.debug(r)
                if ans is None:
                    tts.say("上手く聞こえませんでした")
                    return
                elif not ans:
                    tts.say("わかりました，操作をキャンセルします")
                    return

                tts.say('テレビを操作します')
                irkit.post_messages(data)
            else:
                irkit.post_messages(data)

        elif platform == "tts":
                tts.say(data)
