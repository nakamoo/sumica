import pymongo
from pymongo import MongoClient
from abc import ABC, abstractmethod

client = MongoClient('localhost', 27017)

hai_db = client.hai

class Actor(ABC):

	@abstractmethod
	def observe_state(self, state):
		pass

	@abstractmethod
	def observe_action(self, action):
		pass

	@abstractmethod
	def act(self, state):
		pass

	@abstractmethod
	def rebuild(self):
		pass