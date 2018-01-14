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
        for act in acts:
            print(">>", act['platform'])
            if "platform" in act and "data" in act:
                if "confirmation" in act:
                    if act['confirmation'] is not None:
                        ans = confirm(act['confirmation'])
                        data_confirm = {'action': json.dumps(act),'user_name': self.user, 'answer': ans}
                        r = requests.post("%s/data/confirmation" % self.ip, data=data_confirm, verify=False)
                        logging.debug(r)
                        if ans is None:
                            tts.say("上手く聞こえませんでした")
                            return
                        elif not ans:
                            tts.say("わかりました，操作をキャンセルします")
                            return

                        tts.say('テレビを操作します')
                        irkit.post_messages(act['data'])
                    else:
                        irkit.post_messages(act['data'])

                elif act['platform'] == "tts":
                        tts.say(act['data'])
