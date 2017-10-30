#!/usr/bin/env python
# coding: utf-8

import requests
import json
import configparser
import subprocess
import os
from subprocess import Popen
from subprocess import STDOUT, check_output, TimeoutExpired
import asyncio


class IrkitInternetAPI:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_path = os.path.dirname(os.path.abspath(__file__)) + '/irkit.ini'
        self.config.read(self.config_path)

        self.endpoint = "http://" + self.config['DEFAULT']['ip']
        self.loop = asyncio.get_event_loop()

    def set_param(self):
        print("TVリモコンをIRKitに向けて，on/offボダンを押して下さい")
        input("準備ができたらどれかキーを押して下さい")
        param_tv = self.get_messages()
        self.config['TV']['param'] = param_tv

        print("エアコンのリモコンをIRKitに向けて，on/offボダンを押して下さい")
        input("準備ができたらどれかキーを押して下さい")
        param_ac = self.get_messages()
        self.config['AirConditioning']['param'] = param_ac

        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)

        print("設定に成功しました")

    def get_messages(self):
        headers = {'X-Requested-With': "curl"}
        url = self.endpoint + "/messages"

        r = requests.get(url, headers=headers)
        while (r.text == '') or (r.status_code != 200):
            print("エラー：　もう一度IRKitにむけてリモコンを操作して下さい")
            input("準備ができたらどれかキーを押して下さい")
            r = requests.get(url, headers=headers)

        return r.text

    def post_messages(self, data):
        device = data[0]
        params = self.config[device]['param']
        params = "'" + params + "'"
        cmd = 'curl -i "http://192.168.10.143/messages" -H "X-Requested-With: curl" -d ' + params
        subprocess.Popen(cmd, shell=True)


if __name__ == '__main__':
    irkit = IrkitInternetAPI()
    irkit.set_param()
    # irkit.post_messages('AirConditioning')
    # irkit.post_messages('TV')
