from subprocess import Popen
import subprocess
import json

def do_action(app, cmd):
	if app == "youtube":
		print("OPENING YOUTUBE")
		Popen("node utils/youtube.js {}".format(cmd), shell=True)
	elif app == "shell":
		Popen("{}".format(cmd), shell=True)
	elif app == "print":
		print(cmd)
	elif app == "sound":
		Popen("play ../sounds/{}".format(cmd), shell=True)
	elif app == "hue":
		with open('utils/hue_state.json', 'w+') as outfile:
		    json.dump(json.loads(cmd), outfile)

		out = subprocess.check_output(['node', 'utils/hue.js', 'set_state'])
		print(out.decode('utf-8'))