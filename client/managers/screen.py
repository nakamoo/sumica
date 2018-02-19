import cv2
import time

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
                    conf = "{0:.3g}".format(last["predictions"]["confidence"])
                    cv2.putText(image, "{}: {}".format(last["predictions"]["label"], conf), (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    cv2.imshow("screen", image)
            
            cv2.waitKey(30)

    def close(self):
         cv2.destroyAllWindows()