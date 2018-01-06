import numpy as np
import controllers.vectorizer.vectorizer as vectorizer
#from controllers.vectorizer import utils

def area(b):
    return (b[2]-b[0])*(b[3]-b[1])

class Person2Vec(vectorizer.Vectorizer):
    def __init__(self):
        pass
    
    def vectorize(self, imdata, get_meta=False):
        pose_mat = []
        act_mat = []
        meta = []
        n_cams = len(imdata[0])
        
        for scene in imdata:
            scene_pose_vec = []
            scene_act_vec = []
            scene_meta = []
            
            for view in scene:
                act_vec = np.zeros(1024)
                pose_vec = np.zeros(18*3)
                top_person = None
                
                for det in view["detections"]:
                    if det["label"] == "person" and "passed" in det and "pose_body_index" in det:
                        if top_person is None or area(det["box"]) > area(top_person["box"]):
                            top_person = det
                 
                if top_person is not None:
                    pose_vec = np.array(view["pose"]["body"][top_person["pose_body_index"]]).flatten()
                    
                    if "action_vector" in top_person:
                        act_vec = np.array(top_person["action_vector"])
                        
                scene_pose_vec.append(pose_vec)
                scene_act_vec.append(act_vec)
                scene_meta.append(top_person)
            
            pose_mat.append(np.concatenate(scene_pose_vec))
            act_mat.append(np.concatenate(scene_act_vec))
            meta.append(scene_meta)
            
        if get_meta:
            return np.array(pose_mat), np.array(act_mat), meta
        else:
            return np.array(pose_mat), np.array(act_mat)