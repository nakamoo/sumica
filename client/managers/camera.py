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
            self.enabled = False

        self.image = None
        self.imdata = []
        self.thresh = None
        
        self.last_processed = None
        self.connection = False

        addr = "ws://homeai.ml:5002/predict_ws".format(server_ip)
        self.ws = websocket.WebSocketApp(addr,
                              on_message = self.on_message)
        #sdelf.ws = websocket.WebSocket()
        # self.ws.connect(addr)
 
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

            if not self.connection:
                self.last_processed = {"image": self.image}

            time.sleep(0.03)

    def start(self):
        if not self.enabled:
            return

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

    def send(self, image, thresh, ip):
        uid = uuid.uuid4()
        img_fn = "assets/tmp/image_{}-{}.jpg".format(self.cam_name, uid)
        #diff_fn = "assets/tmp/diff_{}-{}.jpg".format(self.cam_name, uid)

        cv2.imwrite(img_fn, image)

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
            self.connection = True
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
