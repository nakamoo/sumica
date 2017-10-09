import subprocess
import time
import json
import datetime
import requests
import traceback

class Manager:
    def __init__(self, user, server_ip, actions):
        print("connecting to any Hue devices...")
        out = subprocess.check_output(['node', './utils/hue.js', 'connect'])
        out = out.decode('utf-8')
        self.server_ip = server_ip
        self.user = user
        self.send = True
        self.actions = actions
        self.last_manual_time = 0
        self.last_state = None

        if out.split("\n")[-2] != "ok":
            self.connected = False
            print("failed to connect Hue; internet connection or press button?")
        else:
            self.connected = True
            print("connected to Hue.")

    def execute(self, acts):
        for act in acts:
            try:
                if act["platform"] == "send_hue":
                    self.send = act["data"] == "True"
            except Exception as e:
                print(e)

    def check_override(self, current, last_update):
        if last_update["data"] is None:
            return False

        current = {light["id"]: light["state"] for light in current["lights"]}
        last_update = {light["id"]: light["state"] for light in last_update["data"]}
        
        for i, state in current.items():
            a = last_update[i]
            b = state

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
                state = json.loads(state)
                data = {}
                data["lights"] = json.dumps(state["lights"])
                data["time"] = time.time()
                data["user_name"] = self.user

                state_changed = False

                if not self.last_state:
                    self.last_state = state
                elif self.last_state != state:
                    state_changed = True
                    self.last_state = state

                if state_changed:
                    if self.actions.hue_overridden:
                        override = True
                    else:
                        override = self.check_override(state, self.actions.last_hue_update)
                else:
                    override = False

                print("state change", state_changed, "override", override)

                if override:
                    print("MANUAL CHANGE DETECTED")
                    data["last_manual"] = 0
                    self.last_manual_time = time.time()
                    self.actions.hue_overridden = True
                else:
                    data["last_manual"] = time.time() - self.last_manual_time

                #if self.send:
                requests.post(self.server_ip + "/data/hue", data=data, verify=False)
                #else:
                #    print("NOT SENDING")

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
                traceback.print_exc()

if __name__ == "__main__":
    cam = Manager(SERVER_IP)
    cam.start()
