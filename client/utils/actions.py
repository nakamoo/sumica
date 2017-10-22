from subprocess import Popen
import subprocess
import json
import time

from utils.irkit import IrkitInternetAPI
irkit = IrkitInternetAPI()

class Actions:
	def __init__(self):
		self.last_hue_update = {"data": None}
		self.hue_overridden = False

	def act_list(self, actions):
		for action in actions:
			if "platform" in action and "data" in action:
				self.act(action["platform"], action["data"])

	def act(self, platform, data):
		if platform == "youtube":
			print("OPENING YOUTUBE")
			Popen("node utils/youtube.js {}".format(data), shell=True)
		elif platform == "shell":
			Popen("{}".format(data), shell=True)
		elif platform == "print":
			print(data)
		elif platform == "sound":
			Popen("play ../sounds/{}".format(data), shell=True)
		elif platform == "hue":
			json_data = json.loads(data)

			if self.last_hue_update["data"] != json_data:
				with open('utils/hue_state.json', 'w+') as outfile:
				    json.dump(json_data, outfile)

				print("setting hue", data)
				out = subprocess.check_output(['node', 'utils/hue.js', 'set_state'])
				print(out.decode('utf-8'))
				self.last_hue_update = {"data":json_data, "time":time.time()}
				self.hue_overridden = False
        elif platform == "irkit":
            for device in data:
                irkit.post_messages(device)