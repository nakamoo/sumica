import pymongo

client = pymongo.MongoClient('localhost', 27017)

db = client.hai

co = db.images

#print("current data:")

#for data in co.find():
#	print(data)

def save(data):
	#print(data)
	co.insert_one(data)