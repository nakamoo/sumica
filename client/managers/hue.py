import subprocess
import time
import json
import datetime
import requests
import traceback
import logging
import sys
from utils.speechrecognition import confirm

class Manager:
    def __init__(self, user, server_ip, actions):
        logging.debug("connecting to any Hue devices...")
        out = subprocess.check_output(['node', './utils/hue.js', 'connect'])
        out = out.decode('utf-8')
        self.server_ip = server_ip
        self.user = user
        self.send = True

        self.program_control = False
        self.program_control_detected = False
        self.last_manual_time = 0
        self.last_state = None
        self.going_back = False
        self.actions = actions

        if out.split("\n")[-2] != "ok":
            self.connected = False
            print("failed to connect Hue; internet connection or press button?")
        else:
            self.connected = True
            print("connected to Hue.")

    def check_state_change(self, current):
        if self.last_state is None:
            return False

        light_ids = {light["id"]: light["state"] for light in current["lights"]}

        for light_id in light_ids:
            def search_by_id(lights, id):
                for l in lights:
                    if l['id'] == id:
                        return l
                return None
            current_light = search_by_id(current['lights'], light_id)
            last_light = search_by_id(self.last_state['lights'], light_id)
            a = current_light['state']
            b = last_light['state']

            if not a["on"]:
                if a["on"] != b["on"]:
                    return True
            else:
                if a["on"] == b["on"] and abs(a["hue"] - b["hue"]) < 100 and abs(a["bri"] - b["bri"]) < 10 and abs(a["sat"] - b["sat"]) < 10:
                    pass
                else:
                    return True
        return False

    def start(self):
        if not self.connected:
            print("HUE NOT CONNECTED")
            return

        while True:
            try:
                out = subprocess.check_output(['node', './utils/hue.js', 'get_state'])
                state = out.decode('utf-8').split("\n")[-2]
                logging.debug(state)

                state = json.loads(state)
                if self.last_state is None:
                    self.last_state = state

                state_changed = self.check_state_change(state)
                if state_changed:
                    self.last_state = state
                    if self.program_control:
                        self.program_control_detected = True
                else:
                    if self.program_control_detected:
                        self.program_control = False
                        self.program_control_detected = False

                data = {}
                data["lights"] = json.dumps(state["lights"])
                data["time"] = time.time()
                data["user_name"] = self.user


                # if state_changed:
                #     if self.manual_change or self.going_back:
                #         override = True
                #     else:
                #         override = self.check_override(state, self.actions.last_hue_update)
                # else:
                #     override = False

                print("send hue: state change", state_changed, ",program control", self.program_control)

                if (not self.program_control) and state_changed:
                    print("MANUAL CHANGE DETECTED")
                    data["last_manual"] = 0
                    self.last_manual_time = time.time()
                else:
                    data["last_manual"] = time.time() - self.last_manual_time

                data["last_manual_time"] =  self.last_manual_time
                data['state_changed'] = state_changed
                data['program_control'] = self.program_control

                if self.send:
                    requests.post(self.server_ip + "/data/hue", data=data, verify=False)

                """
                for light in state["lights"]:
                    if light["state"]["reachable"]:
                        data = light
                        data["time"] = time.time()
                        #data["utc_time"] = datetime.datetime.utcfromtimestamp(time.time()).strftime('%Y/%m/%d %H:%M:%S')
                        data["user_name"] = self.user
                        try:
                            r = requests.post(self.server_ip + "/data/hue",
                                data=data)
                        except Exception as e:
                            time.sleep(1)
                            print(e)
                 """

                time.sleep(5)
            except:
                logging.warn("error in sending hue data")

if __name__ == "__main__":
    pass
