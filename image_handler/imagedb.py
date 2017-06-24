import pymongo

client = pymongo.MongoClient('localhost', 27017)

db = client.imagedb

co = db.image_means

print("current data:")

for data in co.find():
	print(data)

def save(path, data):
	print(path, data)
	co.insert_one({"path": path, "mean": data})