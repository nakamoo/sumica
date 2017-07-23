states = []
det = 0
last_time = 0

def has_object(obj_class, state):
	for obj in state["detections"]:
		if obj["label"] == obj_class:
			return True

	return False

def act(act, state):
	global det

	last_time = state["time"]

	if has_object("person", state):
		states.append(1)
	else:
		states.append(0)

	t = 10
	if sum(states[-t:]) == t and det == 0:
		act.append({"app":"sound", "cmd":"button83.mp3"})
		det = 1
	elif sum(states[-t:]) == 0 and det == 1:
		act.append({"app":"print", "cmd":"person gone"})
		det = 0

	if len(states) > 100:
		del states[0]