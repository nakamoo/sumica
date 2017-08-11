<<<<<<< HEAD
from controller import Controller
=======
from .controller import Controller
>>>>>>> 51dc6f4fbe4d9ab54040be0de66deab2b692ebb3
import numpy as np

class Detection(Controller):
    def __init__(self):
    	pass

    def on_event(self, event, data):
    	if event == "image":
    		print("image received")
    		print(data)

    		addr = "http://localhost:5002/detect"

    		r = requests.post(addr, files={'image': open("images/" + data["filename"], "rb")}, data=data)

        	print("detections: {}".format(r.text))

    def execute(self):
        return "turn off"

