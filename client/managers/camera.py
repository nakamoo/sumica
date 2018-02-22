import requests
import cv2
import threading
import time
import json
import colorsys
# import managers.flow as flow
import skimage.measure
import numpy as np
import traceback
import urllib
import logging
import websocket
import base64
import uuid
import os


"""
var PTZ_UP=0;
var PTZ_UP_STOP=1;
var PTZ_DOWN=2;
var PTZ_DOWN_STOP=3;
var PTZ_LEFT=4;
var PTZ_LEFT_STOP=5;
var PTZ_RIGHT=6;
var PTZ_RIGHT_STOP=7;
var PTZ_LEFT_UP=90;
var PTZ_RIGHT_UP=91;
var PTZ_LEFT_DOWN=92;
var PTZ_RIGHT_DOWN=93;
var PTZ_STOP=1;

var PTZ_CENTER=25;
var PTZ_VPATROL=26;
var PTZ_VPATROL_STOP=27;
var PTZ_HPATROL=28;
var PTZ_HPATROL_STOP=29;


"""

CAM_UP = 0
CAM_DOWN = 2
CAM_LEFT = 4
CAM_RIGHT = 6
CAM_LEFT_UP = 90
CAM_RIGHT_UP = 91
CAM_LEFT_DOWN = 92
CAM_RIGHT_DOWN = 93
CAM_STOP = 1

def visualize(frame, all_boxes, win_name="frame"):
    for result in all_boxes:
        det = result["box"]
        name = result["label"]

        i = sum([ord(x) for x in name])
        c = colorsys.hsv_to_rgb(i % 100.0 / 100.0, 1.0, 0.9)
        c = tuple([int(x * 255.0) for x in c])
        cv2.putText(frame, name, (det[0], det[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, c, 2)
        cv2.rectangle(frame, (det[0], det[1]), (int(det[2]), int(det[3])), c, 2)

    return frame


class Manager:
    def __init__(self, user, server_ip):
        self.mans = []

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
        self.maxdata = 10
        self.cam_addr = cam_loc

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
                if password is None:
                    password = "password"

                print(requests.get(
                    cam_loc + "/camera_control.cgi?loginuse=admin&loginpas={}&param=15&value=0".format(password)).text)
                print(requests.get(
                    cam_loc + "/set_misc.cgi?loginuse=admin&loginpas={0}&ptz_patrol_rate=10&ptz_patrol_up_rate={1}" +
                              "&ptz_patrol_down_rate={1}&ptz_patrol_left_rate={1}&ptz_patrol_right_rate={1}".format(
                        password, 3)).text)
                self.stream = urllib.request.urlopen(cam_loc + "/videostream.cgi?user=admin&pwd=" + password)
                self.password = password

                print(self.stream)

        except:
            traceback.print_exc()

        self.image = None
        self.imdata = []
        self.thresh = None
        
        self.last_processed = None
        
        addr = "ws://homeai.ml:5002/predict_ws".format(server_ip)
        self.ws = websocket.WebSocketApp(addr,
                              on_message = self.on_message)
        #self.ws = websocket.WebSocket()
        #self.ws.connect(addr)
        
        def run_loop():
            while True:
                self.ws.run_forever()
        
        thread_stream = threading.Thread(target=run_loop)
        thread_stream.daemon = True
        thread_stream.start()

    def close(self):
        if self.camtype == "webcam":
            self.cap.release()
        elif self.camtype == "vstarcam":
            pass
        
        self.ws.close()
        
    def on_message(self, ws, message):
        print("message received")
        data = json.loads(message)
        
        if os.path.exists(data['impath']):
            self.last_processed = {"image": cv2.imread(data['impath']), "predictions": data["predictions"]}
            os.remove(data['impath'])

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
                        if a != -1 and b != -1:
                            jpg = bytes[a:b + 2]
                            bytes = bytes[b + 2:]
                            frame = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8).copy(), cv2.IMREAD_COLOR)
                            #frame = cv2.resize(frame, (frame.shape[1]//10, frame.shape[0]//10))
                            
                            break
                except:
                    traceback.print_exc()
                    logging.warn("frame error")

            if frame is None:
                time.sleep(1)
                continue
                # ret, frame = self.cap.read()
                # if frame is None:
                #    break

            self.image = frame

            gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (7, 7), 0)
            self.imdata.append({"bgr": self.image, "smoothgray": gray})
            if len(self.imdata) > self.maxdata:
                self.imdata = self.imdata[-self.maxdata:]

            time.sleep(0.1)

    def start(self):
        if self.camtype == "webcam":
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800);
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600);

        thread_stream = threading.Thread(target=self.capture_loop)
        thread_stream.daemon = True
        thread_stream.start()
        
        while True:
            if self.image is None:
                time.sleep(1)
                logging.warn('camera {} is down?'.format(self.cam_name))
                continue

            if len(self.imdata) < 2:
                time.sleep(1)
                logging.warn('buffer is too small...')
                continue

            skip = False

            frameDelta = cv2.absdiff(self.imdata[-2]["smoothgray"], self.imdata[-1]["smoothgray"])
            thresh = cv2.threshold(frameDelta, 5, 255, cv2.THRESH_BINARY)[1]
            thresh = skimage.measure.block_reduce(thresh, (4, 4), np.max)

            if np.sum(thresh) < 2000:
                skip = True

            self.movecam()

            if not skip:
                k = cv2.waitKey(1)

                if k == 27:
                    break
                    
                def send_imdata():
                    self.send(self.image, thresh, self.server_ip)

                #thread_stream = threading.Thread(target=send_imdata)
                #thread_stream.daemon = True
                #thread_stream.start()
                send_imdata()
                
                #time.sleep(0.3)
                # 恐らく早すぎてdetection serverに負荷がかかってエラーが生じている
                time.sleep(0.01)
            else:
                print("image skipped.")
                time.sleep(1)

                if not self.enabled:
                    print("webcam failure; exit.")
                    break

        cv2.destroyAllWindows()

    def movecam(self):
        bgr = self.imdata[-1]["bgr"]
        gray = self.imdata[-1]["smoothgray"]
        return

        lower, upper = np.array([0, 0, 100]), np.array([100, 100, 255])

        #mask = cv2.inRange(bgr, lower, upper)
        mask = cv2.absdiff(self.imdata[-2]["smoothgray"], self.imdata[-1]["smoothgray"])
        mask = cv2.threshold(mask, 5, 255, cv2.THRESH_BINARY)[1]

        cmd = CAM_STOP
        mag = 10

        print(np.sum(mask))
        if np.sum(mask) > 1000:
            M = cv2.moments(mask)
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            cX /= mask.shape[1]
            cY /= mask.shape[0]

            moveX, moveY = 0, 0

            print(cX, cY)

            if cY < 0.45:
                moveY = -1
            elif cY > 0.55:
                moveY = 1

            if cX < 0.45:
                moveX = -1
            elif cX > 0.55:
                moveX = 1

            #mag = int(np.sqrt((0.5-cX)**2.0 + (0.5-cY)**2.0) * 20.0)
            #print("mag:", mag)

            if moveX == 0 and moveY < 0:
                cmd = CAM_UP
                print("U")
            elif moveX > 0 and moveY < 0:
                cmd = CAM_RIGHT_UP
                print("RU")
            elif moveX > 0 and moveY == 0:
                cmd = CAM_RIGHT
                print("R")
            elif moveX > 0 and moveY > 0:
                cmd = CAM_RIGHT_DOWN
                print("RD")
            elif moveX == 0 and moveY > 0:
                cmd = CAM_DOWN
                print("D")
            elif moveX < 0 and moveY > 0:
                cmd = CAM_LEFT_DOWN
                print("LD")
            elif moveX < 0 and moveY == 0:
                cmd = CAM_LEFT
                print("L")
            elif moveX < 0 and moveY < 0:
                cmd = CAM_LEFT_UP
                print("LU")

        requests.get(
            self.cam_addr + "/decoder_control.cgi?loginuse=admin&loginpas={}&command={}&onestep=0".format(self.password, cmd))
        requests.get(
            self.cam_addr + "/set_misc.cgi?loginuse=admin&loginpas={0}&ptz_patrol_rate={1}&ptz_patrol_up_rate={1}&ptz_patrol_down_rate={1}&ptz_patrol_left_rate={1}&ptz_patrol_right_rate={1}".format(
                self.password, mag))

    def send(self, image, thresh, ip):
        uid = uuid.uuid4()
        img_fn = "assets/tmp/image_{}-{}.jpg".format(self.cam_name, uid)
        #diff_fn = "assets/tmp/diff_{}-{}.jpg".format(self.cam_name, uid)

        cv2.imwrite(img_fn, image)
        #cv2.imwrite(diff_fn, thresh)

        files = {}
        data = {"user_name": self.user, "time": time.time(), "cam_id": self.cam_name}

        data["motion_update"] = "True"
        data['image'] = base64.b64encode(open(img_fn, "rb").read()).decode("utf-8")
        data['impath'] = img_fn
        #files['image'] = open(img_fn, "rb")
        #files["diff"] = open(diff_fn, "rb")

        try:
            start_time = time.time()
            addr = "{}/predict".format(ip)
            
            
            #print("sending...")
            data = json.dumps(data)
            
            t = time.time()
            self.ws.send(data)
            #print("sent ", time.time() - t, len(data))
            #t = time.time()
            #result = self.ws.recv()
            #print("sent2 ", time.time() - t, len(result))

            #r = requests.post(addr, files=files, data=data, verify=False)
            # result=r.text
            logging.debug("cam {}: sent image to server. Response time: {}".format(self.cam_name, time.time() - start_time))
            
            #self.last_processed = {"image": image, "predictions": json.loads(result)["predictions"]}
            
        except:
            traceback.print_exc()
            logging.error("{}: could not send image to server".format(self.cam_name))
            
        #os.remove(img_fn)
        #os.remove(diff_fn)


if __name__ == "__main__":
    cam = Manager("sean", '', None)
    cam.start()
    time.sleep(30)
    cam.close()
