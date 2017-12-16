import numpy as np
import controllers.vectorizer.vectorizer as vectorizer
#from controllers.vectorizer import utils

class Person2Vec(vectorizer.Vectorizer):
    def __init__(self):
        pass
    
    def vectorize(self, imdata):
        mat = []
        n_cams = len(imdata[0])
        
        for scene in imdata:
            scene_vec = []
            
            for view in scene:
                vec = np.zeros(18*3)
                
                for det in view["detections"]:
                    if det["label"] == "person" and det["passed"] and "pose_body_index" in det:
                        vec = np.array(view["pose"]["body"][det["pose_body_index"]]).flatten()
                        break
                        
                scene_vec.append(vec)
            
            mat.append(np.concatenate(scene_vec))
            
        return np.array(mat)