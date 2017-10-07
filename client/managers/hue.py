import subprocess
import time
import json
import datetime
import requests

class Manager:
    def __init__(self, user, server_ip):
        print("connecting to any Hue devices...")
        out = subprocess.check_output(['node', './utils/hue.js', 'connect'])
        out = out.decode('utf-8')
        self.server_ip = server_ip
        self.user = user
        self.send = True

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

    def start(self):
        if not self.connected:
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
                if self.send:
                    print(data)
                    requests.post(self.server_ip + "/data/hue", data=data)
                else:
                    print("NOT SENDING")

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

                time.sleep(10)
            except:
                pass

if __name__ == "__main__":
    cam = Manager(SERVER_IP)
    cam.start()
