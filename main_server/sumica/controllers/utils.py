import os
import cv2
import colorsys
import numpy as np
from utils import db
from config import Config
import pymongo
import traceback
from PIL import Image
from io import BytesIO
import base64
import uuid

keypoint_labels = [
    "Nose",
    "Neck",
    "RShoulder",
    "RElbow",
    "RWrist",
    "LShoulder",
    "LElbow",
    "LWrist",
    "RHip",
    "RKnee",
    "RAnkle",
    "LHip",
    "LKnee",
    "LAngle",
    "REye",
    "LEye",
    "REar",
    "LEar",
    "Bkg"
]

def impath2base64(impath, scale=0.5, quality=50):
    with BytesIO() as output:
        with Image.open(impath) as img:
            img = img.resize((int(img.width * scale), int(img.height * scale)))
            img.save(output, "JPEG", quality=quality)
        bytedata = output.getvalue()

        encoded_string = base64.b64encode(bytedata)
        encoded_string = encoded_string.decode("utf-8")

        return encoded_string

def saveimgtostatic(imname, impath, scale=0.5, quality=50):
    imname = "s{}-q{}-{}".format(scale, quality, imname)
    path = os.path.join("static", "images", imname)

    if not os.path.exists(path):
        with Image.open(impath) as img:
            img = img.resize((int(img.width * scale), int(img.height * scale)))
            img.save(path, "JPEG", quality=quality)

    return path

def safe_next(imgs):
    while True:
        img = imgs.next()
        try:
            Image.open(Config.RAW_IMG_DIR + img["filename"]).verify()
            break
        except Exception as e:
            traceback.print_exc()
    return img

def get_current_images(user, cam_ids):
    db = get_db()
    
    images = []
    for id in cam_ids:
        imgs = db.images.find({'user_name': user, 'cam_id': id, 'detections': {'$exists': True},
                                  'pose':{'$exists': True}},
                                 sort=[("_id", pymongo.DESCENDING)]).limit(10)

        images.append(safe_next(imgs))

    return images

def get_avg_pt(seq):
    n = 0
    mx, my = 0, 0
    for x, y, c in chunker(seq, 3):
        if c >= 0.05:
            mx += x
            my += y
            n += 1

    if n > 0:
        mx /= n
        my /= n

        return [mx, my]
    else:
        return None

def chunker(seq, size):
  return (seq[pos:pos+size] for pos in range(0, len(seq), size))

def box_contains_pose(box, body_pose):
    count = 0
    
    for x, y, c in body_pose:
        if c > 0.05 and (x >= box[0] and x <= box[2] and y >= box[1] and y <= box[3]):
            count += 1
        
    return count

def iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    # compute the area of intersection rectangle
    interArea = (xB - xA + 1) * (yB - yA + 1)

    # compute the area of both the prediction and ground-truth
    # rectangles
    boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
    boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)

    # compute the intersection over union by taking the intersection
    # area and dividing it by the sum of prediction + ground-truth
    # areas - the interesection area
    iou = interArea / float(boxAArea + boxBArea - interArea)

    # return the intersection over union value
    return iou

def sort_persons(data):
    dets = data["detections"]
    poses = data["pose"]["body"]
    results = []
    
    for pose_i, pose in enumerate(poses):
        # find best matching box for each pose
        best_index = None
        best_count = 0
        best_area = 9999999

        indices = [r[0] for r in results]

        for i, det in enumerate(dets):
            if i not in indices and det["label"] == "person":
                count = box_contains_pose(det["box"], pose)
                b = det["box"]
                area = (b[3]-b[1])*(b[2]-b[0])
                if best_index is None:
                    best_index, best_count, best_area = i, count, area
                elif count > best_count:
                    best_index, best_count, best_area = i, count, area
                elif count == best_count and area < best_area:
                    best_index, best_count, best_area = i, count, area
        
        if best_index is not None:
            results.append([best_index, pose_i, dets[best_index]["confidence"]])

    indices = [r[0] for r in results]
    for i, det in enumerate(dets):
        if i not in indices and det["label"] == "person":
            results.append([i, -1, dets[i]["confidence"]])

    # sort by pose first, then detection confidence
    results = sorted(results, key=lambda x: (int(x[1] is None), -x[2]))
    results = [{"det_index": r[0], "pose_index": r[1]} for r in results]

    return results
    
def draw_object(frame, result):
            det = result["box"]
            name = result["label"] + ": " + "%.2f" % result["confidence"]
            
            

            if "passed" in result and not result["passed"]:
                return

            i = sum([ord(x) for x in result["label"]])
            c = colorsys.hsv_to_rgb(i%100.0/100.0, 1.0, 0.9)
            c = tuple([int(x * 255.0) for x in c])

            #cv2.rectangle(frame, (det[0], det[1]), (int(det[2]), int(det[3])), c, 2)
            
            label_offsetx = det[0]

            if "passed" in result:
                name += "; " + result["action"] + ": " + "%.2f" % result["action_confidence"]
                act_box = result["action_crop"]
                
                label_offsetx = act_box[0]
                cv2.rectangle(frame, (act_box[0], act_box[1]), (int(act_box[2]), int(act_box[3])), c, 2)
                cv2.rectangle(frame, (det[0], det[1]), (int(det[2]), int(det[3])), c, 1)
            else:
                cv2.rectangle(frame, (det[0], det[1]), (int(det[2]), int(det[3])), c, 2)

            cv2.rectangle(frame, (label_offsetx, det[1]-20), (label_offsetx+len(name)*10, det[1]), c, -1)
            cv2.rectangle(frame, (label_offsetx, det[1]-20), (label_offsetx+len(name)*10, det[1]), (0, 0, 0), 1)
            cv2.putText(frame, name, (label_offsetx+5, det[1]-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

def draw_pose(frame, person):
    body_lines = [[0, 1], [1, 2], [2, 3], [3, 4], [1, 5], [5, 6], [6, 7], [0, 14], [14, 16], [0, 15], [15, 17], [1, 8], [8, 9], [9, 10], [1, 11], [11, 12], [12, 13]]
    
    for i, (pt1_i, pt2_i) in enumerate(body_lines):
            pt1 = person[pt1_i]
            pt2 = person[pt2_i]

            if pt1[2] < 0.05 or pt2[2] < 0.05:
                continue

            a = np.array([[[i*20, 255, 255]]], dtype=np.uint8)
            col = cv2.cvtColor(a, cv2.COLOR_HSV2BGR)[0][0]
            col = (int(col[0]), int(col[1]), int(col[2]))
            cv2.circle(frame, (int(pt1[0]), int(pt1[1])), 5, col, -1)
            cv2.circle(frame, (int(pt2[0]), int(pt2[1])), 5, col, -1)
            cv2.line(frame, (int(pt1[0]), int(pt1[1])), (int(pt2[0]), int(pt2[1])), col, 2)
            
def visualize(frame, summ, draw_objects=True):
    for result in summ["detections"]:
        if not draw_objects and result["label"] != "person":
                continue
        draw_object(frame, result)
        
    for person in summ["pose"]["body"]:
        draw_pose(frame, person)
            
    """
    for person in summ["pose"]["face"]:
        for x, y, c in person:
            if c > 0.05:
                cv2.circle(frame, (int(x), int(y)), 3, (0, 255, 0), -1)
                
    for person in summ["pose"]["hand"]:
        for x, y, c in person:
            if c > 0.05:
                cv2.circle(frame, (int(x), int(y)), 3, (0, 255, 0), -1)
    """

    return frame
