import pickle
from .controller import Controller
from controllers.learner import datasets
import json

def in_row(history, row, target):
    for i in range(row):
        if history[-i] != target:
            return False
    return True

class ActivityTest2(Controller):
    def __init__(self, user):
        self.user = user
        self.history = []
        data = pickle.load(open("classifier.pkl", "rb"))
        self.classifier = data["classifier"]
        self.classes = data["classes"]
        self.preprocessor = data["preprocessor"]
        self.action = None

    def on_event(self, event, data):
        if event == "summary":
            summ = data["summary"]
            touch_classes = ["cell phone","laptop","book", "keyboard"]
            
            vec = datasets.summary2vec(touch_classes, touch_classes, summ, incl_touch=True, incl_look=False, incl_dist=False, incl_pose=False, incl_hand=False)
            vec = self.preprocessor.transform([vec])
            pred = self.classifier.predict(vec)
            pred = self.classes[pred[0]]
            #pred_vec = [int(i == pred) for i in range(len(self.classes))]
            self.history.append(pred)
            
            if len(self.history) >= 3:
                if pred == "nothing":
                    if in_row(self.history, 3, "nothing"):
                        self.action = pred
                elif pred == "noone":
                    if in_row(self.history, 3, "noone"):
                        self.action = pred
                elif self.history[-1] == self.history[-2]:
                    self.action = pred
                
            print(">PREDICTION:", pred)
            
    def execute(self):
        b, s, h = (255, 100, 30000)
        
        if self.action == "laptop":
            b, s, h = (200, 255, 33000)
        elif self.action == "phone":
            b, s, h = (200, 144, 13544)
        elif self.action == "nothing":
            b, s, h = (121, 254, 15324)
        
        re = [{"platform": "hue", "data": json.dumps({"on": True, "hue": h, "sat": s, "bri": b})}]
        return re