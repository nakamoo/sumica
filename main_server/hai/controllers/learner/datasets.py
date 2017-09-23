import numpy as np
import json
from pymongo import MongoClient

# x depends on summaries
# y is hue state
# includes very rule-based features
def get_hue_dataset1(username, start_time, end_time, cam_id, incl_touch=True, incl_look=True, incl_dist=True, incl_pose=True, incl_hand=True):
    client = MongoClient()
    mongo = client.hai
    
    query = {"user_name": username, "cam_id": str(cam_id), "summary":{"$exists": True}, "time": {"$gt": start_time, "$lt": end_time}}
    n = mongo.images.find(query).sort([("time",-1)])
    image_data = list(n)

    query = {"user_name": "sean", "time": {"$gt": start_time, "$lt": end_time}}
    n = mongo.hue.find(query).sort([("time",-1)])
    hue_data = list(n)
    
    touch_list, look_list = get_objects(image_data)
    #touch_classes = list(set(touch_list))
    #look_classes = list(set(look_list))
    touch_classes = ["cell phone","laptop","book", "keyboard"]
    look_classes = touch_classes
    
    print(len(image_data), "images")
    print(len(hue_data), "hue data")
    
    if "None" in look_classes:
        look_classes.remove("None")
    
    light_ids = get_light_ids(hue_data)
    
    tags = [data["tag"] for data in image_data]
    dataX = np.array([summary2vec(touch_classes, look_classes, data["summary"], incl_touch, incl_look, incl_dist, incl_pose, incl_hand) for data in image_data])
    dataY = np.array([hue2vec(data, light_ids) for data in hue_data])
    
    return dataX, dataY, tags, touch_classes, look_classes

def get_light_ids(data):
    ids = []
    
    for d in data:
        lights = json.loads(d["lights"])
        for light in lights:
            if light["state"]["reachable"]:
                ids.append(light["id"])
    
    return list(set(ids))

def hue2vec(data, light_ids):
    lights = json.loads(data["lights"])
    dpl = 4 # dimensions per light
    
    vec = np.zeros(len(light_ids) * dpl)
    for light in lights:
        state = light["state"]
        if light["id"] in light_ids:
            i = light_ids.index(light["id"])
            if state["reachable"]:
                vec[i*dpl:(i+1)*dpl] = [int(state["on"]), state["hue"] / 65535.0, state["sat"] / 255.0, state["bri"] / 255.0]
            
    return vec

def summary2vec(touch_classes, look_classes, summary, incl_touch=True, incl_look=True, incl_dist=True, incl_pose=True, incl_hand=True):
    person_exists = 0
    touch_vec = np.zeros(len(touch_classes))
    look_vec = np.zeros(len(look_classes))
    pose_vec = np.zeros(18*3)
    hand_vec = np.zeros(126)
    #brightness = data["brightness"]
    main_person = [None, 0]

    for obj in summary:
        if obj["label"] == "person":
            person_exists = 1
            if obj["confidence"] > main_person[1]:
                main_person = [obj, obj["confidence"]]
                
            if "keypoints" in obj and obj["keypoints"] is not None:
                pose_vec = np.array(obj["keypoints"]["pose_keypoints"])
                hand_vec = np.array(obj["keypoints"]["hand_right_keypoints"] + obj["keypoints"]["hand_left_keypoints"])
            
            if "touching" in obj:
                for t_obj in obj["touching"]:
                    if t_obj in touch_classes:
                        touch_vec[touch_classes.index(t_obj)] = 1
                if obj["looking"] in look_classes and obj["looking"] and obj["looking"] != "None":
                    look_vec[look_classes.index(obj["looking"])] = 1
                    
    dist_vec = np.zeros([len(touch_classes), 3])
    #if main_person[0] is not None:
    #    main_person = main_person[0]
    #    pb = main_person["box"]
    #    main_pt = np.array([(pb[0]+pb[2])/2.0, (pb[1]+pb[3])/2.0])
        
    for obj in summary:
            if obj != main_person:
                if obj["label"] in touch_classes:
                    b = obj["box"]
                    obj_pt = np.array([(b[0]+b[2])/2.0, (b[1]+b[3])/2.0])
                    #dist = np.sum((main_pt-obj_pt)**2.0)
                    dist = obj_pt#main_pt - obj_pt
                    dist_vec[touch_classes.index(obj["label"])] = np.concatenate([np.array([1]), dist])
    
    dist_vec = dist_vec.flatten()
        
    fin_vec = [[person_exists]]
    if incl_touch:
        fin_vec.append(touch_vec)
    if incl_look:
        fin_vec.append(look_vec)
    if incl_dist:
        fin_vec.append(dist_vec)
    if incl_pose:
        fin_vec.append(pose_vec)
    if incl_hand:
        fin_vec.append(hand_vec)
        
    return np.concatenate(fin_vec)
    
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

def filter_tags(rawDataX, tags, y_classes=None):
    if y_classes is None:
        y_classes = ["phone", "nothing", "laptop", "noone"]
    #    y_classes = list(set(tags))
        
    #if "?" in y_classes: y_classes.remove("?")
    #if "" in y_classes: y_classes.remove("")
    #if "" in y_classes: y_classes.remove("")
    
    dataX = []
    dataY = []
    for x, tag in zip(rawDataX, tags):
        if tag in y_classes:
            dataX.append(x)
            dataY.append(y_classes.index(tag))
        
    dataX = np.array(dataX)
    dataY = np.array(dataY)
    
    return dataX, dataY, y_classes