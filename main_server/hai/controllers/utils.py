import cv2
import colorsys

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

def filter_persons(data, det_threshold=0.8):
    # detection passes if it contains pose or confidence is above threshold
    dets = data["detections"]
    poses = data["pose"]["body"]
    indices = []
    pose_indices = []
    
    for pose_i, pose in enumerate(poses):
        # find best matching box for each pose
        best_index = None
        best_count = 0
        best_area = 9999999
        
        for i, det in enumerate(dets):
            if i not in indices and det["label"] == "person":
                count = box_contains_pose(det["box"], pose)
                b = det["box"]
                area = (b[3]-b[1])*(b[2]-b[0])
                if best_index is None:
                    best_index, best_count, best_area = i, count, area
                elif count >= best_count:
                    if count > best_count:
                        best_index, best_count, best_area = i, count, area
                    elif area < best_area:
                        best_index, best_count, best_area = i, count, area
        
        if best_index is not None:
            indices.append(best_index)
            pose_indices.append(pose_i)
            
    for i, det in enumerate(dets):
        if i not in indices and det["confidence"] >= det_threshold:
            indices.append(i)
            pose_indices.append(None)
                    
    return indices, pose_indices

def visualize(frame, summ):
    for result in summ["detections"]:
        det = result["box"]
        name = result["label"] + ": " + "%.2f" % result["confidence"]
        
        if "passed" in result and not result["passed"]:
            continue

        i = sum([ord(x) for x in result["label"]])
        c = colorsys.hsv_to_rgb(i%100.0/100.0, 1.0, 0.9)
        c = tuple([int(x * 255.0) for x in c])
        
        cv2.rectangle(frame, (det[0], det[1]), (int(det[2]), int(det[3])), c, 2)
        
        if "passed" in result:
            name += "; " + result["action"] + ": " + "%.2f" % result["action_confidence"]
            act_box = result["action_crop"]
            cv2.rectangle(frame, (act_box[0], act_box[1]), (int(act_box[2]), int(act_box[3])), c, 2)
            
        cv2.putText(frame, name, (det[0], det[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, c, 2)

    for person in summ["pose"]["body"]:
        for x, y, c in person:
            if c > 0.05:
                cv2.circle(frame, (int(x), int(y)), 3, (0, 255, 0), -1)
            #if result["label"] == "person" and result["pose"] is not None:
            #  def draw_pts(pts, col):
            #    for x, y, c in chunker(pts, 3):
            #      if c > 0.05:
            #        cv2.circle(frame, (int(x), int(y)), 3, col, -1)

            #  #draw_pts(result["pose"]["body"], (0, 255, 0))
            #  #draw_pts(result["pose"]["hand_left_keypoints"], (255, 0, 0))
            #  #draw_pts(result["pose"]["hand_right_keypoints"], (255, 0, 0))
            
    for person in summ["pose"]["face"]:
        for x, y, c in person:
            if c > 0.05:
                cv2.circle(frame, (int(x), int(y)), 3, (0, 255, 0), -1)
                
    for person in summ["pose"]["hand"]:
        for x, y, c in person:
            if c > 0.05:
                cv2.circle(frame, (int(x), int(y)), 3, (0, 255, 0), -1)

    return frame
