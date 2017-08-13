from subprocess import Popen
import subprocess
import json

def act_list(actions):
	for action in actions:
		if "platform" in action and "data" in action:
			act(action["platform"], action["data"])

def act(platform, data):
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
		with open('utils/hue_state.json', 'w+') as outfile:
		    json.dump(json.loads(data), outfile)

		out = subprocess.check_output(['node', 'utils/hue.js', 'set_state'])
		print(out.decode('utf-8'))