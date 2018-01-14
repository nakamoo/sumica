from subprocess import Popen
import subprocess
import json
import time
import requests
import logging

from utils.irkit import IrkitInternetAPI
from utils.speechrecognition import confirm, confirm_and_post_result
from actors.actor import Actor
import utils.tts as tts

irkit = IrkitInternetAPI()

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
                        phrases = [
                            'テレビを操作します',
                            'わかりました，操作をキャンセルします',
                            '上手く聞こえませんでした'
                        ]
                        approved = confirm_and_post_result(act, self.user, self.ip, phrases)
                        if not approved:
                            return

                        irkit.post_messages(act['data'])
                    else:
                        irkit.post_messages(act['data'])

                elif act['platform'] == "tts":
                        tts.say(act['data'])
