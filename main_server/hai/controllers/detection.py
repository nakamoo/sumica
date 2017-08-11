from .controller import Controller
import numpy as np

class Detection(Controller):
    def __init__(self):
    	pass

    def on_event(self, event, data):
    	if event == "image":
    		print("image received")
    		print(data)

    def execute(self):
        return "turn off"

