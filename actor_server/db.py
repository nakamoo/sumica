import pymongo

client = pymongo.MongoClient('localhost', 27017)

db = client.hai

def save_image_data(data):
	db.images.insert_one(data)

def save_hue_data(data):
	db.hue.insert_one(data)

def save_youtube_data(data):
	db.youtube.insert_one(data)
