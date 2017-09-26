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

def visualize(frame, summ):
    for result in summ:
        det = result["box"]
 
        if result["label"] == "person" and result["keypoints"] is not None:
          def draw_pts(pts, col):
            for x, y, c in chunker(pts, 3):
              if c > 0.05:
                cv2.circle(frame, (int(x), int(y)), 3, col, -1)
          
          draw_pts(result["keypoints"]["pose_keypoints"], (0, 255, 0))
          draw_pts(result["keypoints"]["hand_left_keypoints"], (255, 0, 0))
          draw_pts(result["keypoints"]["hand_right_keypoints"], (255, 0, 0))

        name = result["label"] + ": " + "%.2f" % result["confidence"]

        i = sum([ord(x) for x in result["label"]])
        c = colorsys.hsv_to_rgb(i%100.0/100.0, 1.0, 0.9)
        c = tuple([int(x * 255.0) for x in c])
        cv2.putText(frame, name, (det[0], det[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, c, 2)
        cv2.rectangle(frame, (det[0], det[1]), (int(det[2]), int(det[3])), c, 2)

    return frame
