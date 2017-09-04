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
