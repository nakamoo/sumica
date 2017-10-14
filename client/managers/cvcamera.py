import requests
import cv2
import threading
import time
import json
import colorsys
#import managers.flow as flow
import skimage.measure
import numpy as np
import traceback

def visualize(frame, all_boxes, win_name="frame"):
    for result in all_boxes:
        det = result["box"]
        name = result["label"]

        i = sum([ord(x) for x in name])
        c = colorsys.hsv_to_rgb(i%100.0/100.0, 1.0, 0.9)
        c = tuple([int(x * 255.0) for x in c])
        cv2.putText(frame, name, (det[0], det[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, c, 2)
        cv2.rectangle(frame, (det[0], det[1]), (int(det[2]), int(det[3])), c, 2)
    
    return frame

cv2.namedWindow("image", cv2.WINDOW_NORMAL)

class Manager:
    def __init__(self, user, server_ip, actions):
        self.mans = []

        with open("cameras.txt", "r") as f:
            lines = f.readlines()
            for line in lines:
                tokens = line.split()
                self.mans.append(CamManager(user, server_ip, tokens[1], tokens[2], tokens[0]))
        
    def start(self):
        for man in self.mans:
            if man.enabled:
                thread_stream = threading.Thread(target=man.start)
                thread_stream.daemon = True
                thread_stream.start()

    def close(self):
        for man in self.mans:
            man.cap.release()
            print("releasing", man.cam_name)

class CamManager:
    def __init__(self, user, server_ip, cam_loc, cam_name, camtype, detect_only=False):
        self.server_ip = server_ip
        self.enabled = True
        self.detect_only = detect_only
        self.user = user
        self.cam_name = cam_name
        self.camtype = camtype

        print("camera:", camtype, cam_name, cam_loc)

        try:
            if camtype == "webcam":
                self.cap = cv2.VideoCapture(int(cam_loc))
            elif camtype == "vstarcam":
                print(requests.get(cam_loc + "/camera_control.cgi?loginuse=admin&loginpas=password&param=15&value=0").text)
                print(cam_loc + "/videostream.cgi?user=admin&pwd=password")
                self.cap = cv2.VideoCapture(cam_loc + "/videostream.cgi?user=admin&pwd=password")

            print("cam detected:", cam_loc, self.cap.isOpened())
            #self.enabled = self.cap.isOpened()
            #if not self.enabled:
            #  self.cap.release()
        except Exception as e:
            traceback.print_exc()

        self.image = None
        self.image1, self.image2 = None, None
        self.thresh = None

    def capture_loop(self):
        while True:
            ret, frame = self.cap.read()

            if frame is None:
                print(self.cam_name, ": frame is none")
                time.sleep(1)
                continue
                #ret, frame = self.cap.read()
                #if frame is None:
                #    break

            self.image = frame

            def update_image():
                gray1 = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
                gray1 = cv2.GaussianBlur(gray1, (7, 7), 0)
                self.image1 = [self.image, gray1]

            if self.image1 is None:
                update_image()
            else:
                self.image2 = self.image1
                update_image()
            
            time.sleep(0.1)

    def start(self):
        if not self.enabled:
            return

        if self.camtype == "webcam":
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800);
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600);

        thread_stream = threading.Thread(target=self.capture_loop)
        thread_stream.daemon = True
        thread_stream.start()
   
        #cv2.namedWindow("capture", cv2.WINDOW_NORMAL)
        last_img = None
        diff_thres = 0.5

        while True:
            if self.image is None or self.image1 is None or self.image2 is None:
                time.sleep(1)
                continue

            skip = False
	
            frameDelta = cv2.absdiff(self.image1[1], self.image2[1])
            thresh = cv2.threshold(frameDelta, 5, 255, cv2.THRESH_BINARY)[1]
            thresh = skimage.measure.block_reduce(thresh, (4, 4), np.max)

            if not skip:
                #cv2.imshow("capture", self.image)
                #last_img = gray
                k = cv2.waitKey(1)

                if k == 27:
                    break
		    
                try:
                    if self.detect_only:
                        self.show(self.image, self.server_ip)
                    else:
                        self.send(self.image, thresh, self.server_ip)
                except Exception as e:
                    print("unable to send image to server.")
                    print(e)
        
                time.sleep(0.1)
            else:
                print("image not captured.")
                time.sleep(1)

                if not self.enabled:
                    print("webcam failure; exit.")
                    break

        cv2.destroyAllWindows()

    def send(self, image, thresh, ip):
        cv2.imwrite("image.png", image)
        cv2.imwrite("diff.png", thresh)

        #print(image)
        cv2.imshow("image", image)
        cv2.waitKey(1)

        data = {"user_name": self.user, "time": time.time(), "cam_id": self.cam_name}
        addr = "{}/data/images".format(ip)
        print("sending image to:", addr)
        files = {}
        files['image'] = open("image.png", "rb")
        files["diff"] = open("diff.png", "rb")

        r = requests.post(addr, files=files, data=data, verify=False)

    def show(self, image, ip):
        cv2.imwrite("image.png", image)

        data = {"threshold": "0.5"}
        addr = "{}/detect".format(ip)
        r = requests.post(addr, files={'image': open("image.png", "rb")}, data=data, verify=False)

        print(r.text)

        frame = visualize(image, json.loads(r.text)["objects"])
        cv2.imshow("dets", frame)
        cv2.waitKey(1)

if __name__ == "__main__":
    cam = Manager("sean", '', None)
    cam.start()
    time.sleep(10)
    cam.close()