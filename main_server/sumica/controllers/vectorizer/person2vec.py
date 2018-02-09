import numpy as np

import controllers.vectorizer.vectorizer as vectorizer
from controllers.utils import sort_persons

def area(b):
    return (b[2]-b[0])*(b[3]-b[1])

def normalize_pose(pose_matrix):
    # pose matrix is (18x3)
    pose_matrix[:, :2] -= pose_matrix[1, :2]
    return pose_matrix


class Person2Vec(vectorizer.Vectorizer):
    def __init__(self):
        pass
    
    def vectorize(self, imdata, get_meta=False, average=False):
        pose_mat = []
        act_mat = []
        meta = []
        
        for scene in imdata:
            scene_pose_vec = []
            scene_act_vec = []
            scene_meta = []
            
            for view in scene:
                act_vec = np.zeros(1024)
                pose_vec = np.zeros(18*3)

                if len(view["persons"]) > 0:
                    if average:
                        poses = 0
                        dets = 0

                        for person in view["persons"]:
                            det_index = person["det_index"]
                            pose_index = person["pose_index"]
                            top_person = view["detections"][det_index]

                            if pose_index >= 0:
                                pose_vec += normalize_pose(np.array(view["pose"]["body"][pose_index])).flatten() * top_person["confidence"]
                                poses += 1

                            if det_index >= 0:
                                act_vec += np.array(top_person["action_vector"]) * top_person["confidence"]
                                dets += 1

                        if poses > 0:
                            pose_vec /= poses

                        if dets > 0:
                            act_vec /= dets

                        scene_meta.append([0])
                    else:
                        det_index = view["persons"][0]["det_index"]
                        pose_index = view["persons"][0]["pose_index"]
                        top_person = view["detections"][det_index]

                        if "pose_body_index" in top_person: # doesnt contain if no filter
                            pose_vec = normalize_pose(np.array(view["pose"]["body"][pose_index])).flatten()

                        if "action_vector" in top_person:
                            act_vec = np.array(top_person["action_vector"])
                        scene_meta.append([0])
                else:
                    scene_meta.append([-1])
                        
                scene_pose_vec.append(pose_vec)
                scene_act_vec.append(act_vec)

            
            pose_mat.append(np.concatenate(scene_pose_vec))
            act_mat.append(np.concatenate(scene_act_vec))
            meta.append(scene_meta)
            
        if get_meta:
            return np.array(pose_mat), np.array(act_mat), meta
        else:
            return np.array(pose_mat), np.array(act_mat)