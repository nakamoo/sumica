import pymongo
from pymongo import MongoClient
import json
import cv2
import numpy as np
import datetime
from sklearn import neighbors
from subprocess import call
from subprocess import Popen
import actionmanager as acts

client = MongoClient('localhost', 27017)

hai_db = client.hai

images = hai_db.images
actions = hai_db.actions

class Dataset:
	def __init__(self):
		self.update()

	def transform(self, x):
		dets = json.loads(x["detections"])

		max_area = 0
		pt = None
		for det in dets:
			if det["label"] == "person":
				#print(det)
				area = (det["box"][2]-det["box"][0])*(det["box"][3]-det["box"][1])
				if area > max_area:
					cX = (det["box"][0] + det["box"][2]) / 2.0
					cY = (det["box"][1] + det["box"][3]) / 2.0
					max_area = area
					pt = (cX, cY)

		return pt

	def update(self):
		self.X = []
		self.Y = []
		tmpX = []
		tmpY = []
		y_names = []

		for action in actions.find():
			isoDate = action["time"]
			before = isoDate - datetime.timedelta(seconds=10)#minutes=1)
			results = images.find({"time":{"$gte": before, "$lt": isoDate}})

			for r in results:
				tmpX.append(r)
				tmpY.append(action)

		for img, y in zip(tmpX, tmpY):
			pt = self.transform(img)

			if pt:
				self.X.append([pt[0], pt[1]])
				y_names.append(y["action"])

		self.class_names = list(set(y_names))

		for y in y_names:
			self.Y.append(self.class_names.index(y))

class Actor:
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

				acts.execute(msg)

			if len(self.action_history) > 100:
				self.action_history = self.action_history[-50:]
