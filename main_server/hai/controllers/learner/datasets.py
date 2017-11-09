import numpy as np
import json
from pymongo import MongoClient
import time
import operator
import random
import scipy.misc
import cv2

from imgaug import augmenters as iaa

port = 1111

def generate_image_event_dataset(image_data, print_data, num_cams, feat_gen, augs=1):
    dataX, dataY = [], []
    imagesX = []
    summs = []
    classes = list(set([y["text"] for y in print_data]))

    for x, y in zip(image_data, print_data):
        for imgs in x:
            row = []
            row_images = []
            skip = False

            for cam in imgs:
                if cam is not None:
                    test_img = scipy.misc.imread("./images/raw_images/" +  cam["filename"])
                    if test_img is None or len(test_img.shape) != 3:
                        skip = True
                        break
                        
                    row_images.append(cam)
                else:
                    skip = True
                    break
            if not skip:
                imagesX.append(row_images)
                dataY.append(classes.index(y["text"]))
                
    img_batch = []

    for t in imagesX:
        for img in t:
            mat = scipy.misc.imread("./images/raw_images/" +  img["filename"])
            mat = scipy.misc.imresize(mat, (224, 224))
            img_batch.append(mat)
            summs.append(img)
            
    from PIL import Image
    times = augs
    aug_imgs = augment_images(img_batch, times)
    aug_imgs_pil = [Image.fromarray(img) for img in aug_imgs]

    vecs = feat_gen(aug_imgs_pil, summs*times)
    vecs = np.array(vecs)
    
    #samples = sum([len(x) for x in image_data])
    mat = vecs.reshape([-1,vecs.shape[1]*num_cams])
    
    return mat, dataY*times, classes

def augment_images(img_batch, times):
    images = []
    
    """
    seq = iaa.Sequential([
        iaa.GaussianBlur(sigma=(0, 3.0)), # blur images with a sigma of 0 to 3.0
        iaa.Add((-10, 10), per_channel=0.5), # change brightness of images (by -10 to 10 of original value)
        iaa.AddToHueAndSaturation((-20, 20)),
    ])
    """
    seq = iaa.Sequential([
        iaa.Fliplr(0.5), # horizontal flips
        iaa.Crop(percent=(0, 0.1)), # random crops
        # Small gaussian blur with random sigma between 0 and 0.5.
        # But we only blur about 50% of all images.
        iaa.Sometimes(0.5,
            iaa.GaussianBlur(sigma=(0, 0.5))
        ),
        # Strengthen or weaken the contrast in each image.
        iaa.ContrastNormalization((0.75, 1.5)),
        iaa.Grayscale(alpha=(0.0, 1.0)),
        # Add gaussian noise.
        # For 50% of all images, we sample the noise once per pixel.
        # For the other 50% of all images, we sample the noise per pixel AND
        # channel. This can change the color (not only brightness) of the
        # pixels.
        iaa.AdditiveGaussianNoise(loc=0, scale=(0.0, 0.05*255), per_channel=0.5),
        # Make some images brighter and some darker.
        # In 20% of all cases, we sample the multiplier once per channel,
        # which can end up changing the color of the images.
        iaa.Multiply((0.8, 1.2), per_channel=0.2),
        # Apply affine transformations to each image.
        # Scale/zoom them, translate/move them, rotate them and shear them.
        iaa.Affine(
            scale={"x": (0.8, 1.2), "y": (0.8, 1.2)},
            translate_percent={"x": (-0.2, 0.2), "y": (-0.2, 0.2)},
            rotate=(-25, 25),
            shear=(-8, 8)
        )
    ], random_order=True)

    for i in range(times):
        print("{}/{}".format(i, times))
        images_aug = seq.augment_images(img_batch)
        images.extend(images_aug)
        
    return images

def get_event_images(username, event_data, cam_names, start_offset=0, end_offset=60, stride=5, size=10, skip=False, with_summary=True):
    client = MongoClient('localhost', port)
    mongo = client.hai
    
    image_data = []
    for data in event_data:
        data2 = []
        start_time = int(data["time"]+start_offset)
        end_time = int(data["time"]+end_offset)

        for s in range(start_time, end_time-size, stride):
            interval_data = []
            incomplete = False

            for cam in cam_names:
                
                query = {"user_name": username, "cam_id": cam, "time": {"$gte": s, "$lt": s+size}}
                if with_summary:
                    query["summary"] = {"$exists": with_summary}
                
                n = mongo.images.find(query)

                if n.count() > 0:
                    interval_data.append(n[0])
                else:
                    interval_data.append(None)
                    incomplete = True

            if skip and incomplete:
                pass
            else:
                data2.append(interval_data)
        image_data.append(data2)
    return image_data

def get_hue_dataset2(username, start_time=None, end_time=None, top_classes=5, max_samples=-1,
                    incl_touch=False, incl_look=False, incl_dist=False, incl_pose=False, incl_hand=False, incl_feats=True):
    img_data = list(get_image_data(username, start_time, end_time, sort_order=1))
    hue_data = get_hue_data(username, start_time, end_time, sort_time=1)
    
    print(len(hue_data))
    
    if max_samples > 0:
        sample_indices = random.sample(range(len(img_data)), max_samples)
        sample_indices.sort(reverse=True)
        img_data = [img_data[i] for i in sample_indices]
    
    #image_features = [np.load("./image_features/" + fn["image_features_filename"]) for fn in img_data]
    #image_features = [summary2vec([], [], data["summary"], False, False, False, True, False, True) for data in img_data]
    #image_features = [summary2vec([], [], data["summary"], False, False, False, True, False, False) for data in img_data]
    

    new_img_data, new_hue_data = connect_hue_image(img_data, hue_data)
    
    image_features = [data2vec([], [], data,
                                  incl_touch, incl_look, incl_dist, incl_pose, incl_hand, incl_feats) for data in new_img_data]
    new_hue_data, n_lights = reshape_hue_data(new_hue_data)
    hue_classes, labels, counts = get_hue_labels(new_hue_data, top_classes)
    
    return image_features, labels, hue_classes, counts

def connect_hue_image(img_data, hue_data):
    hue_index = 0
    new_img_data = []
    new_hue_data = []
    
    for img in img_data:
        while img["time"] >= hue_data[hue_index]["time"]:
            hue_index += 1
            if hue_index >= len(hue_data):
                break
                
        if hue_index >= len(hue_data):
                break
            
        if hue_data[hue_index]["time"] - img["time"] < 10:
            new_img_data.append(img)
            new_hue_data.append(hue_data[hue_index])
    
    return new_img_data, new_hue_data

def get_image_data(username, start_time=None, end_time=None, cam_id=0, sort_order=-1):
    client = MongoClient('localhost', port)
    mongo = client.hai
    
    if start_time is None:
        start_time = time.time() - 600 #10 min
    if end_time is None:
        end_time = time.time()
    
    query = {"user_name": username, "cam_id": str(cam_id), "summary":{"$exists": True}, "time": {"$gt": start_time, "$lt": end_time}}
    n = mongo.images.find(query).sort([("time",sort_order)])
    
    return n

def reshape_hue_data(data):
    n_lights = max([len(d["lights"]) for d in data])
    re = np.zeros([len(data), n_lights*5])
    for i, d in enumerate(data):
        for k, light in enumerate(d["lights"]):
            if light["on"] and light["reachable"]:
                re[i, k*5:(k+1)*5] = [light["reachable"], light["on"], light["hue"], light["sat"], light["bri"]]
            else:
                re[i, k*5:(k+1)*5] = [0, 0, 0, 0, 0]
            
    return re, n_lights

def get_hue_labels(data_mat, top_classes=5):
    classes = list(set([tuple(row) for row in data_mat]))
    n_classes = len(classes)
    
    indices = [classes.index(tuple(row)) for row in data_mat]
    counts = np.array([indices.count(i) for i in range(n_classes)])
    
    count_dict = {index:count for index, count in zip(range(n_classes), counts)}
    sorted_counts = sorted(count_dict.items(), key=operator.itemgetter(1), reverse=True)
    top_classes = [classes[i] for i, n in sorted_counts[:top_classes]]
    sorted_counts = [(classes[i], n) for i, n in sorted_counts]
    
    indices = []
    
    for row in data_mat:
        tup = tuple(row)
        
        if tup in top_classes:
            indices.append(top_classes.index(tup))
        else:
            indices.append(len(top_classes))
            
    return top_classes, indices, sorted_counts

def get_hue_data(username, start_time, end_time, sort_time=-1, manual=None):
    client = MongoClient('localhost', port)
    mongo = client.hai
    
    if manual is None:
        query = {"user_name": username, "time": {"$gt": start_time, "$lt": end_time}}
    else:
        query = {"user_name": username, "time": {"$gt": start_time, "$lt": end_time}, "last_manual": {"$gt": manual[0], "$lt": manual[1]}}
    n = mongo.hue.find(query).sort([("time", sort_time)])
    
    re = []
    
    for data in n:
        lights = json.loads(data["lights"])
        row = {}
        row_lights = []

        for light in lights:
            state = light["state"]
            state = {"reachable": state["reachable"], "on": state["on"], "hue": state["hue"], "sat": state["sat"], "bri": state["bri"]}
            row_lights.append(state)
            
        row["lights"] = row_lights
        row["time"] = data["time"]
        re.append(row)
    
    return re

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
    dataX = np.array([data2vec(touch_classes, look_classes, data, incl_touch, incl_look, incl_dist, incl_pose, incl_hand) for data in image_data])
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

def data2vec(touch_classes, look_classes, data, incl_touch=True, incl_look=True, incl_dist=True, incl_pose=True, incl_hand=True, incl_feats=False):
    person_exists = 0
    touch_vec = np.zeros(len(touch_classes))
    look_vec = np.zeros(len(look_classes))
    pose_vec = np.zeros(18*3)
    hand_vec = np.zeros(126)
    #brightness = data["brightness"]
    main_person = [None, 0]
    
    summary = data["summary"]

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
    if incl_feats:
        feats = np.load("./image_features/" + data["image_features_filename"]) 
        fin_vec.append(feats)
        
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