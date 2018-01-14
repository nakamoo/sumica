import subprocess
import time
import json
import datetime
import requests
import traceback
import logging
import sys
from utils.speechrecognition import confirm, confirm_and_post_result

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
                        phrases = [
                            '照明を操作します',
                            'わかりました，操作をキャンセルします',
                            '上手く聞こえませんでした'
                        ]
                        approved = confirm_and_post_result(act, self.user, self.ip, phrases)
                        if not approved:
                            return

                    json_data = json.loads(act['data'])
                    with open('utils/hue_state.json', 'w+') as outfile:
                        json.dump(json_data, outfile)
                    out = subprocess.check_output(['node', 'utils/hue.js', 'set_state'])

            except Exception as e:
                traceback.print_exc()
                print(e)

