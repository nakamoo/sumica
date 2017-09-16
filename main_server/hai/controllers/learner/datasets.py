import numpy as np
import json
from pymongo import MongoClient

# x depends on summaries
# y is hue state
# includes very rule-based features
def get_hue_dataset1(username, start_time, cam_id):
    client = MongoClient()
    mongo = client.hai
    
    query = {"user_name": username, "cam_id": str(cam_id), "summary":{"$exists": True}, "time": {"$gt": start_time}}
    n = mongo.images.find(query).sort([("time",-1)])
    image_data = list(n)

    query = {"user_name": "sean", "time": {"$gt": start_time}}
    n = mongo.hue.find(query).sort([("time",-1)])
    hue_data = list(n)
    
    touch_list, look_list = get_objects(image_data)
    touch_classes = list(set(touch_list))
    look_classes = list(set(look_list))
    look_classes.remove("None")
    
    light_ids = get_light_ids(hue_data)
    
    dataX = np.array([data2vec(touch_classes, look_classes, data) for data in image_data])
    dataY = np.array([hue2vec(data, light_ids) for data in hue_data])
    
    return dataX, dataY, touch_classes, look_classes

def get_light_ids(data):
    ids = []
    
    for d in data:
        lights = json.loads(d["lights"])
        for light in lights:
            ids.append(light["id"])
    
    return list(set(ids))

def hue2vec(data, light_ids):
    lights = json.loads(data["lights"])
    dpl = 4 # dimensions per light
    
    vec = np.zeros(len(light_ids) * dpl)
    for light in lights:
        state = light["state"]
        i = light_ids.index(light["id"])
        if state["reachable"]:
            vec[i*dpl:(i+1)*dpl] = [int(state["on"]), state["hue"] / 65535.0, state["sat"] / 255.0, state["bri"] / 255.0]
            
    return vec

def data2vec(touch_classes, look_classes, data):
    person_exists = 0
    touch_vec = np.zeros(len(touch_classes))
    look_vec = np.zeros(len(look_classes))
    #brightness = data["brightness"]
    main_person = [None, 0]

    for obj in data["summary"]:
        if obj["label"] == "person":
            person_exists = 1
            if obj["confidence"] > main_person[1]:
                main_person = [obj, obj["confidence"]]
            
            if "touching" in obj:
                for t_obj in obj["touching"]:
                    touch_vec[touch_classes.index(t_obj)] = 1
                if obj["looking"] and obj["looking"] != "None":
                    look_vec[look_classes.index(obj["looking"])] = 1
                    
    misc_vec = np.zeros(len(touch_classes))
    if main_person[0] is not None:
        main_person = main_person[0]
        pb = main_person["box"]
        main_pt = np.array([(pb[0]+pb[2])/2.0, (pb[1]+pb[3])/2.0])
        
        for obj in data["summary"]:
            if obj != main_person:
                if obj["label"] in touch_classes:
                    b = obj["box"]
                    obj_pt = np.array([(b[0]+b[2])/2.0, (b[1]+b[3])/2.0])
                    dist = np.sum((main_pt-obj_pt)**2.0)
                    misc_vec[touch_classes.index(obj["label"])] = dist
        
    return np.concatenate([[person_exists], touch_vec, look_vec, misc_vec])
    
def get_objects(data):
    look_all, touch_all = [], []
    for n in data:
        look_objects = []
        touch_objects = []
        for obj in n["summary"]:
            if obj["label"] == "person" and "touching" in obj:
                touch_objects.extend(obj["touching"])
                look_objects.append(obj["looking"])
        look_all.extend(look_objects)
        touch_all.extend(touch_objects)
    return touch_all, look_all