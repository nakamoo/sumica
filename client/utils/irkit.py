#!/usr/bin/env python
# coding: utf-8

import requests
import json
import configparser
import os


class IrkitInternetAPI:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_path = os.path.dirname(os.path.abspath(__file__)) + '/irkit.ini'
        self.config.read(self.config_path)

        self.endpoint = "http://" + self.config['DEFAULT']['ip']

    def set_param(self):
        print("TVリモコンをIRKitに向けて，on/offボダンを押して下さい")
        input("準備ができたらどれかキーを押して下さい")
        param_tv = self.get_messages()
        self.config['TV']['param'] == param_tv

        print("エアコンのリモコンをIRKitに向けて，on/offボダンを押して下さい")
        input("準備ができたらどれかキーを押して下さい")
        param_ac = self.get_messages()
        self.config['AirConditioning']['param'] == param_ac

        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)

        print("OK")

    def get_messages(self):
        headers = {'X-Requested-With': "curl"}
        url = self.endpoint + "/messages"

        r = requests.get(url, headers=headers)
        if (r.text == '') or (r.status_code != 200):
            print("Error. Please retry.")

        return r.text

    def post_messages(self, device):
        message = self.config[device]['param']
        message = json.dumps(message)

        params = {'message': message}

        url = self.endpoint + "/messages"
        headers = {'X-Requested-With': "curl"}
        r = requests.post(url, headers=headers, params=params)


if __name__ == '__main__':
    IrkitInternetAPI().set_param()
