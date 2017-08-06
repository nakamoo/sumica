from subprocess import Popen
import subprocess
import json

def do_action(app, cmd):
	if app == "youtube":
		print("OPENING YOUTUBE")
		Popen("node actions/youtube.js {}".format(cmd), shell=True)
	elif app == "shell":
		Popen("{}".format(cmd), shell=True)
	elif app == "print":
		print(cmd)
	elif app == "sound":
		Popen("play ../sounds/{}".format(cmd), shell=True)
	elif app == "hue":
		with open('actions/hue_state.json', 'w+') as outfile:
		    json.dump(json.loads(cmd), outfile)

		print(subprocess.check_output(['node', 'actions/hue.js', 'set_state']))