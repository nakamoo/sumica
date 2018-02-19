import cv2
import time

class Manager:
    def __init__(self, user, server_ip):
        self.faces = [cv2.imread("assets/face-smile.png"), cv2.imread("assets/face-talk.png")]
        
        cv2.namedWindow("test", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("test", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    def start(self):
        while True:
            cv2.imshow("test", 255 - self.faces[0])
            cv2.waitKey(100)
            cv2.imshow("test", 255 - self.faces[1])
            cv2.waitKey(100)

    def close(self):
        pass