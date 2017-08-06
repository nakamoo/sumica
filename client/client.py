import threading
import json

from sensors.camera import Camera
#from sensors.hue import Hue

import actions

# create ID
# discover hardware (e.g. discover cameras)
# send sensor data
# receive commands and act

SERVER_IP = ""
# hard-code for now
ID = "noguchi"

# hard-code for now
inputs = [Camera(0)]

for inp in inputs:
    threading.Thread(target=inp.start)
    
    thread_stream.daemon = True
    thread_stream.start()

while True:
    r = requests.post(SERVER_IP, data={'id': ID})
    action_data = json.loads(r.text)
    actions.act(action_data)