import subprocess
import time
import json
import datetime
import requests

SERVER_IP = "https://homeai.ml:5001"

class Manager:
    def __init__(self, user, server_ip):
        print("connecting to any Hue devices...")
        out = subprocess.check_output(['node', './utils/hue.js', 'connect'])
        out = out.decode('utf-8')

        if out.split("\n")[-2] != "ok":
            self.connected = False
            print("failed to connect Hue; internet connection or press button?")
        else:
            self.connected = True
            print("connected to Hue.")

    def start(self):
        if not self.connected:
            return        

        while True:
            out = subprocess.check_output(['node', './utils/hue.js', 'get_state'])
            state = json.loads(out.decode('utf-8').split("\n")[-2])

            for light in state["lights"]:
                if light["state"]["reachable"]:
                    data = light
                    data["utc_time"] = datetime.datetime.utcfromtimestamp(time.time()).strftime('%Y/%m/%d %H:%M:%S')
                    data["user_id"] = 'koki'
                    try:
                        r = requests.post(SERVER_IP + "/data/hue",
                                json.dumps(data),
                                headers={'Content-Type': 'application/json'})
                    except Exception as e:
                        time.sleep(1)
                        print(e)

            time.sleep(10)

if __name__ == "__main__":
    cam = Manager(SERVER_IP)
    cam.start()
