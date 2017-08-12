from apps.actor import Actor

on = True

def has_object(obj_class, state):
	for obj in state["detections"]:
		if obj["label"] == obj_class:
			return True

	return False

class HelloActor(Actor):
	def act(self, state):
		global on
		re = []

		if has_object("person", state):
			if not on:
				re.append({"app":"print", "cmd":"hi"})
				#re.append({"app":"sound", "cmd":"button83.mp3"})
				#re.append({"app":"hue", "cmd":'{"bri":255}'})
				on = True
		else:
			if on:
				re.append({"app":"print", "cmd":"bye"})
				#re.append({"app":"hue", "cmd":'{"bri":64}'})
				on = False

		return re