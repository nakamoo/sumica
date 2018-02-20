import cv2
import time
import colorsys

class Manager:
    def __init__(self, user, server_ip, mm):
        self.faces = [cv2.imread("assets/face-smile.png"), cv2.imread("assets/face-talk.png")]
        
        cv2.namedWindow("screen", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("screen", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        
        cv2.setMouseCallback("screen", self.click)
        
        self.mode = 0
        self.mm = mm
        
    def click(self, event, x, y, flags, param):
        if event == 1:
            self.mode += 1
            self.mode = self.mode % (1 + len(self.mm.sensor_mods["camera"].mans))

    def start(self):
        while True:
            if self.mode == 0:
                cv2.imshow("screen", 255 - self.faces[1])
            else:
                #if len(self.mm.sensor_mods["camera"].mans[self.mode-1].imdata) > 0:
                #    cv2.imshow("screen", self.mm.sensor_mods["camera"].mans[self.mode-1].imdata[-1]["bgr"])
                if self.mm.sensor_mods["camera"].mans[self.mode-1].last_processed is not None:
                    last = self.mm.sensor_mods["camera"].mans[self.mode-1].last_processed
                    
                    image = last["image"]
                    conf = "{0:.2g}".format(last["predictions"]["confidence"])
                    cv2.putText(image, "{}: {}".format(last["predictions"]["label"], conf), (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    for det in last["predictions"]["detections"]:
                        box = det["box"]
                        i = sum([ord(x) for x in det["label"]])
                        c = colorsys.hsv_to_rgb(i%100/100.0, 1.0, 0.9)
                        c = tuple([int(x * 255) for x in c])
                        cv2.rectangle(image, (box[0], box[1]), (int(box[2]), int(box[3])), c, 2)
                        conf = "{0:.2g}".format(det["confidence"])
                        cv2.putText(image, "{}: {}".format(det["label"], conf), (box[0] + 10, box[1] + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, c, 2)
                    
                    cv2.imshow("screen", image)
            
            cv2.waitKey(30)

    def close(self):
         cv2.destroyAllWindows()