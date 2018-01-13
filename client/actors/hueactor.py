import subprocess
import time
import json
import datetime
import requests
import traceback
import logging
import sys
from utils.speechrecognition import confirm

from actors.actor import Actor

class HueActor(Actor):
    def __init__(self, user, ip):
        self.user = user
        self.ip = ip

    def execute(self, acts):
        for act in acts:
            try:
                if act['platform'] == "hue":
                    if 'confirmation' in act:
                        print(act['confirmation'])
                        ans = confirm(act['confirmation'])
                        data_confirm = {'platform': act['platform'], 'data': act['data'], 'user_name': self.user,
                                        'confirmation': act['confirmation'], 'answer': ans}
                        r = requests.post("%s/data/confirmation" % self.server_ip, data=data_confirm, verify=False)
                        if ans is None:
                            self.actions.act("tts", "上手く聞こえませんでした")
                            return
                        elif not ans:
                            self.actions.act('tts', "わかりました，操作をキャンセルします")
                            return
                        self.actions.act('tts','照明を操作します')

                    json_data = json.loads(act['data'])
                    with open('utils/hue_state.json', 'w+') as outfile:
                        json.dump(json_data, outfile)
                    out = subprocess.check_output(['node', 'utils/hue.js', 'set_state'])

            except Exception as e:
                traceback.print_exc()
                print(e)

