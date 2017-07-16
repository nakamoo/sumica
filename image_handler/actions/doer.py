from subprocess import Popen

def do_action(app, cmd):
	if app == "youtube":
		print("OPENING YOUTUBE")
		Popen("node actions/youtube.js {}".format(cmd), shell=True)
	elif app == "shell":
		Popen("{}".format(cmd), shell=True)