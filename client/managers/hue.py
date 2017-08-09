import subprocess
import time
import json
import datetime

class Manager:
    def __init__(self, server_ip):
        print("connecting to any Hue devices...")
        out = subprocess.check_output(['node', 'utils/hue.js', 'connect'])
        out = out.decode('utf-8')

        if out.split("\n")[-2] != "ok":
            print("failed to connect Hue; internet connection or press button?")
        else:
            print("connected to Hue.")

    def start(self):
        while True:
            out = subprocess.check_output(['node', 'utils/hue.js', 'get_state'])
            state = json.loads(out.decode('utf-8').split("\n")[-2])

            for light in state["lights"]:
                if light["state"]["reachable"]:
                    data = light
                    data["utc_time"] = datetime.datetime.utcfromtimestamp(time.time())
                    print(data)
                    #apps[1].new_state(data)
                    #db.save_hue_data(data)
                    #print("saved hue data.")
                    #apps[1].update(data)

            time.sleep(10)