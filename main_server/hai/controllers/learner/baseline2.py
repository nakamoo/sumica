import pymongo
from pymongo import MongoClient
from abc import ABC, abstractmethod
import datetime
from apps.actor import Actor
import json
from apps.learner import transformers
from sklearn.neighbors import KNeighborsClassifier
from sklearn import metrics
from sklearn.model_selection import GridSearchCV

client = MongoClient('localhost', 27017)

hai_db = client.hai

class Dataset:
	def __init__(self):
		self.update()

	def update(self):
		X = []
		Y = []
		tmpX = []
		tmpY = []
		y_names = []

		actions = hai_db.hue
		images = hai_db.images

		for action in actions.find():
			if action["auto"]: # do not include datapoints created by system
				continue

			isoDate = action["utc_time"]
			before = isoDate - datetime.timedelta(seconds=5)#minutes=1)
			results = images.find({"utc_time":{"$gte": before, "$lt": isoDate}})

			for r in results:
				tmpX.append(r)
				tmpY.append(action)

		for img, y in zip(tmpX, tmpY):
			pt = transformers.person_rect(img)

			if pt:
				X.append(pt)
				y_names.append(json.dumps(y["state"], sort_keys=True))

		self.class_names = list(set(y_names))
		#print("classes", self.class_names)

		for y in y_names:
			Y.append(self.class_names.index(y))

		self.X = X
		self.Y = Y

class LearningActor(Actor):
	def __init__(self):
		self.data = Dataset()

		tuned_parameters = [{'n_neighbors': [1, 2, 5, 10]}]
		knn = KNeighborsClassifier()
		self.knn = GridSearchCV(knn, tuned_parameters, cv=2,
                       scoring='accuracy')

		self.n_classes = len(self.data.class_names)
		self.last_cmd = None
		self.in_control = False
		self.take_control = False
		self.min_data = 20
		self.current_state = None
		self.needs_fitting = True

		if len(self.data.X) > self.min_data:
			self.knn.fit(self.data.X, self.data.Y)

	def new_state(self, data):
		data["auto"] = self.in_control

	def eq(self, a, b):
		a = json.loads(a)
		b = json.loads(b)

		equal = True

		if a["on"] != b["on"] or abs(a["bri"] - b["bri"]) > 25 or abs(a["sat"] - b["sat"]) > 25 or abs(a["hue"] - b["hue"]) > 2500:
			equal = False

		return equal

	def update(self, hue_state):
		self.current_state = json.dumps(hue_state["state"], sort_keys=True)

		if self.last_cmd is not None and not self.eq(self.last_cmd, self.current_state) and self.in_control:
			print("LOST CONTROL: >>", self.last_cmd, " >> ", self.current_state)
			self.in_control = False
			self.needs_fitting = True

		self.data.update()

		print(len(self.data.class_names) != self.n_classes, self.needs_fitting)

		if len(self.data.X) > self.min_data and (len(self.data.class_names) != self.n_classes or self.needs_fitting):
			self.n_classes = len(self.data.class_names)

			print("refitting...")
			#print(self.data.X)
			self.knn.fit(self.data.X, self.data.Y)
			self.needs_fitting = False

			print("fitted.")

			y_pred_class = self.knn.predict(self.data.X)
			acc = metrics.accuracy_score(self.data.Y, y_pred_class)
			print("training accuracy: ", acc)

			# if validation accuracy > 0.9: take_control = True

	def act(self, state):
		print("AUTO: ", self.in_control, len(self.data.X))

		re = []

		if self.current_state is None:
			return []

		if len(self.data.X) > self.min_data and not self.needs_fitting: # and take_control
			pt = transformers.person_rect(state)
			if pt:
				cmd = self.data.class_names[self.knn.predict([pt])[0]]

				if not self.eq(self.current_state, cmd):
					print("NEW CMD")
					print(self.current_state, " >> ", cmd)
					self.in_control = True
					re.append({"app":"hue", "cmd":cmd})
					self.last_cmd = cmd
					self.current_state = cmd
		
		return re