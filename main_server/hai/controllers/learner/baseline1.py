import json
import cv2
import numpy as np
import datetime
from sklearn import neighbors
from subprocess import call
from subprocess import Popen
from . import actor
import time
import json

class BaselineActor(actor.Actor):
	def __init__(self):
		self.rebuild()
		self.execute = -1
		self.action_history = []

	def rebuild(self):
		print("rebuilding")
		self.dataset = Dataset()

		if len(self.dataset.class_names) <= 0:
			return

		self.clf = neighbors.KNeighborsClassifier(3, 'uniform')
		self.clf.fit(self.dataset.X, self.dataset.Y)

	def observe_state(self, state):
		pass

	def observe_action(self, action):
		self.rebuild()

	def act(self, state):
		if len(self.dataset.class_names) <= 0:
			return

		state = self.dataset.transform(state)

		if state:
			pred_y = self.clf.predict([state])[0]
			self.action_history.append(pred_y)

			repeated = True

			for a, b in zip(self.action_history[-5:-1], self.action_history[-4:]):
				if a != b:
					repeated = False
					break

			if repeated and self.execute != self.action_history[-1]:
				self.execute = self.action_history[-1]
				msg = self.dataset.class_names[self.execute]
				print(msg)

				#Popen(msg, shell=True)
				#acts.execute(msg)

			if len(self.action_history) > 100:
				self.action_history = self.action_history[-50:]

if __name__ == "__main__":
	test = BaselineActor()

	for i in range(100):
		x1, y1 = np.random.randint(600, size=2)
		x2, y2 = x1 + np.random.randint(100), y1 + np.random.randint(100)
		state = {"path": "", "time": time.time()}

		det = [{"label":"person", "box":[int(x1), int(y1), int(x2), int(y2)], "confidence":0.83}]
		state["detections"] = json.dumps(det)

		test.act(state)

		time.sleep(0.1)
		print(i)