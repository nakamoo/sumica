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
import urllib
import logging

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

#cv2.namedWindow("image", cv2.WINDOW_NORMAL)

class Manager:
    def __init__(self, user, server_ip):
        self.mans = []

        try:
            with open("cameras.txt", "r") as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith("#"):
                        continue

                    tokens = line.split()
                    if len(tokens) >= 4:
                        self.mans.append(CamManager(user, server_ip, tokens[1], tokens[2], tokens[0], password=tokens[3]))
                    else:
                        self.mans.append(CamManager(user, server_ip, tokens[1], tokens[2], tokens[0]))
        except:
            exit()

    def start(self):
        for man in self.mans:
            thread_stream = threading.Thread(target=man.start)
            thread_stream.daemon = True
            thread_stream.start()

    def close(self):
        for man in self.mans:
            man.close()
            print("releasing", man.cam_name)


class CamManager:
    def __init__(self, user, server_ip, cam_loc, cam_name, camtype, detect_only=False, password=None):
        self.server_ip = server_ip
        self.enabled = True
        self.detect_only = detect_only
        self.user = user
        self.cam_name = cam_name
        self.camtype = camtype

        logging.debug("camera: {}, {}, {}".format(camtype, cam_name, cam_loc))

        try:
            if camtype == "webcam":
                self.cap = cv2.VideoCapture(int(cam_loc))

                logging.debug("cam detected: {}, {}".format(cam_loc, self.cap.isOpened()))
                self.enabled = self.cap.isOpened()
                if not self.enabled:
                    self.cap.release()
                    print("ERROR opening stream")
            elif camtype == "vstarcam":
                if password is not None:
                    print(cam_loc + "/videostream.cgi?user=admin&pwd=*******")
                    self.stream = urllib.request.urlopen(cam_loc + "/videostream.cgi?user=admin&pwd=" + password)
                else:
                    print(cam_loc + "/videostream.cgi?user=admin&pwd=password")
                    # resize resolution
                    print(requests.get(cam_loc + "/camera_control.cgi?loginuse=admin&loginpas=password&param=15&value=0").text)
                    self.stream = urllib.request.urlopen(cam_loc + "/videostream.cgi?user=admin&pwd=password")
                print(self.stream)

        except Exception as e:
            traceback.print_exc()

        self.image = None
        self.image1, self.image2 = None, None
        self.thresh = None

    def close(self):
        if self.camtype == "webcam":
            self.cap.release()
        elif self.camtype == "vstarcam":
            pass

    def capture_loop(self):
        bytes = b''
        while True:
            if self.camtype == "webcam":
                ret, frame = self.cap.read()
            elif self.camtype == "vstarcam":
                frame = None

                try:
                    while True:
                        bytes += self.stream.read(1024)
                        a = bytes.find(b'\xff\xd8')
                        b = bytes.find(b'\xff\xd9')
                        if a!=-1 and b!=-1:
                            jpg = bytes[a:b+2]
                            bytes= bytes[b+2:]
                            frame = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8).copy(), cv2.IMREAD_COLOR)
                            break
                except:
                    logging.warn("frame error")

            if frame is None:
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
        #if self.enabled:
        #    logging.warn('camera {} is down'.format(self.cam_name))
        #    return

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
                logging.warn('camera {} is down?'.format(self.cam_name))
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
                    logging.warn("unable to send image to server.")
                    logging.warn(e)

                # time.sleep(0.1)
                # 恐らく早すぎてdetection serverに負荷がかかってエラーが生じている
                time.sleep(1)
            else:
                print("image not captured.")
                time.sleep(1)

                if not self.enabled:
                    print("webcam failure; exit.")
                    break

        cv2.destroyAllWindows()

    def send(self, image, thresh, ip):
        img_fn = "image_{}.png".format(self.cam_name)
        diff_fn = "diff_{}.png".format(self.cam_name)

        cv2.imwrite(img_fn, image)
        cv2.imwrite(diff_fn, thresh)

        # cv2.imshow(self.cam_name, image)
        # cv2.waitKey(1)

        try:
            files = {}
            data = {"user_name": self.user, "time": time.time(), "cam_id": self.cam_name}

            #print(np.mean(thresh))
            #if np.mean(thresh) > 10.0:
            data["motion_update"] = "True"
            files['image'] = open(img_fn, "rb")
            files["diff"] = open(diff_fn, "rb")
            #else:
            #    data["motion_update"] = "False"

            addr = "{}/data/images".format(ip)
            t = time.time()

            r = requests.post(addr, files=files, data=data, verify=False)
            logging.debug("cam {}: sent image to server. Response time: {}".format(self.cam_name, time.time()-t))
        except:
            logging.error("{}: could not send image to server".format(self.cam_name))

    def show(self, image, ip):
        cv2.imwrite("image.jpg", image)

        data = {"threshold": "0.5"}
        addr = "{}/detect".format(ip)
        r = requests.post(addr, files={'image': open("image.jpg", "rb")}, data=data, verify=False)

        print(r.text)

        frame = visualize(image, json.loads(r.text)["objects"])
        # cv2.imshow("dets", frame)
        cv2.waitKey(1)

if __name__ == "__main__":
    cam = Manager("sean", '', None)
    cam.start()
    time.sleep(30)
    cam.close()
