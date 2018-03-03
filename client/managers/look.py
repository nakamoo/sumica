import cv2
import time
import requests
import numpy as np
import threading
import logging

#from managers import talk


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
CAM_CENTER = 25

MODE_MOTION = 0
MODE_SCAN = 1
MODE_PRIVATE = 2


class CameraMover:
    def __init__(self, cam, man):
        self.current_cmd = CAM_STOP
        self.last_moved = 0
        self.moving = False
        self.cammag = [0, 0]
        self.info = None
        self.cam = cam

        self.newmode = True
        self.man = man
        self.absent = 100

        self.last_cmd = -1

    def optflow(self, prev, next):
        prev = cv2.resize(prev, (prev.shape[1] // 4, prev.shape[0] // 4))
        next = cv2.resize(next, (next.shape[1] // 4, next.shape[0] // 4))

        hsv = np.zeros_like(prev)
        hsv[..., 1] = 255

        prev = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
        next = cv2.cvtColor(next, cv2.COLOR_BGR2GRAY)

        flow = cv2.calcOpticalFlowFarneback(prev, next, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        flowmag = np.sum(flow ** 2.0, 2)

        mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        hsv[..., 0] = ang * 180 / np.pi / 2
        hsv[..., 2] = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX)
        hsv[flowmag < 0.1, :] = 0
        bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        return flow, flowmag, bgr

    def controlcam(self, onestep, cmd, mag):
        if cmd == CAM_STOP and self.last_cmd == cmd:
            return

        requests.get(
            self.cam.cam_addr + "/set_misc.cgi?loginuse=admin&loginpas={0}&ptz_patrol_rate={1}&ptz_patrol_up_rate={2}&ptz_patrol_down_rate={2}&ptz_patrol_left_rate={1}&ptz_patrol_right_rate={1}".format(
                self.cam.password, mag[0], mag[1]))
        requests.get(
            self.cam.cam_addr + "/decoder_control.cgi?loginuse=admin&loginpas={}&command={}&onestep={}".format(self.cam.password, cmd, onestep))
        self.last_cmd = cmd

    def stopcam(self):
        self.controlcam(0, CAM_STOP, [0, 0])

    def stride(self, cmd, mag, t):
        self.controlcam(0, cmd, mag)

        if t >= 0:
            time.sleep(t)
            self.controlcam(0, CAM_STOP, [0, 0])

    def start(self):
        while True:
            self.update()

    def update(self):
        self.movecam()

    def find_person(self):
        center = None
        pose_found = False
        #found = False
        n = 0

        last = self.cam.data_hist[-1]

        if last is None or last["image"] is None:
            return False, None

        if "predictions" in last:
            for body in last['predictions']['pose']['body']:
                for x, y, c in body:
                    #found = True

                    if center is None:
                        center = [0, 0]

                    center[0] += x * c
                    center[1] += y * c
                    n += c
                    pose_found = True

            for det in last['predictions']['object']:
                if det['label'] == 'person' and det['confidence'] > 0.95:
                    #found = True

                    if not pose_found:
                        if center is None:
                            center = [0, 0]

                        b = det['box']
                        c = det['confidence']

                        center[0] += (b[0] + b[2] / 2) * c
                        center[1] += (b[1] + b[3] / 2) * c
                        n += c

        if n > 0:
            center = [center[0] / n, center[1] / n]

        found = []

        for data in self.cam.data_hist[-5:]:
            f = False

            for body in data['predictions']['pose']['body']:
                for x, y, c in body:
                    if c > 0.1:
                        f = True
                        break

                if f:
                    break

            if not f:
                for det in data['predictions']['object']:
                    if det['label'] == 'person' and det['confidence'] > 0.95:
                        f = True

            found.append(f)

        return found, center

    def movecam(self):
        onestep = 0

        if self.man.mode == MODE_MOTION:
            if self.newmode:
                #self.controlcam(onestep, CAM_CENTER, [10, 10])
                #time.sleep(50)
                #self.controlcam(onestep, CAM_STOP, [10, 10])

                self.newmode = False

            last = self.cam.last_processed
            if last is None or 'predictions' not in last:
                return

            found, center = self.find_person()

            if found[-1]:
                self.absent = 0
            else:
                self.absent += 1

            if self.absent > 20:
                self.info = {"mode": "scan", "text": "resetting"}
                self.controlcam(0, CAM_LEFT_DOWN, [10, 10])
                time.sleep(13)

                mode = CAM_RIGHT
                done = False
                ystrides = 3
                #hist = []
                done = False

                for y in range(ystrides):
                    for x in range(10):
                        self.stride(mode, [10, 10], 1)
                        #time.sleep(1)
                        found, _ = self.find_person()
                        #hist.append(int(found))

                        self.info = {"mode": "scan", "text": "scanning... {} {} {}".format(found[-1], x, sum(found))}

                        if sum(found) >= 4:
                            done = True
                            self.absent = 0

                            if mode == CAM_RIGHT:
                                self.stride(CAM_LEFT, [10, 10], 1)
                            elif mode == CAM_LEFT:
                                self.stride(CAM_RIGHT, [10, 10], 1)

                            break

                    if y != ystrides-1:
                        self.stride(CAM_UP, [10, 10], 1)

                    if done:
                        self.info = {"mode": "scan", "text": "person spotted"}
                        self.stopcam()
                        break

                    if mode == CAM_RIGHT:
                        mode = CAM_LEFT
                    elif mode == CAM_LEFT:
                        mode = CAM_RIGHT

            elif center is None:
                self.stopcam()
                self.info = {"text": "absent: {}".format(self.absent)}
                time.sleep(0.5)
            else:
                cmd = CAM_STOP
                moveX, moveY = 0, 0

                cX = center[0] / last["image"].shape[1]
                cY = center[1] / last["image"].shape[0]

                margin = 0.2

                if cY < 0.5-margin or cY > 0.5+margin or cX < 0.5-margin or cX > 0.5+margin:
                    if cY < 0.5:
                        moveY = -1
                    elif cY > 0.5:
                        moveY = 1

                    if cX < 0.5:
                        moveX = -1
                    elif cX > 0.5:
                        moveX = 1

                def calcm(xx):
                    diff = abs(0.5 - cX)
                    if diff > 0.3:
                        return int(diff*20)
                    else:
                        return int(diff*1)

                self.cammag = [max(calcm(cX), 1), max(calcm(cY), 1)]
                # print("mag:", mag)

                if moveX == 0 and moveY < 0:
                    cmd = CAM_UP
                elif moveX > 0 and moveY < 0:
                    cmd = CAM_RIGHT_UP
                elif moveX > 0 and moveY == 0:
                    cmd = CAM_RIGHT
                elif moveX > 0 and moveY > 0:
                    cmd = CAM_RIGHT_DOWN
                elif moveX == 0 and moveY > 0:
                    cmd = CAM_DOWN
                elif moveX < 0 and moveY > 0:
                    cmd = CAM_LEFT_DOWN
                elif moveX < 0 and moveY == 0:
                    cmd = CAM_LEFT
                elif moveX < 0 and moveY < 0:
                    cmd = CAM_LEFT_UP

                self.info = {"center": center, "move": [moveX, moveY], "speed": self.cammag, "text": "absent: {}".format(self.absent)}

                self.stride(cmd, self.cammag, -1)
                #time.sleep(0.1)

        elif self.man.mode == MODE_PRIVATE:
            if self.newmode:
                #self.controlcam(cam.cam_addr, cam.password, onestep, CAM_CENTER, [10, 10])
                #time.sleep(50)
                self.controlcam(onestep, CAM_UP, [10, 10])
                time.sleep(10)
                self.controlcam(onestep, CAM_STOP, [10, 10])

                self.newmode = False

class Manager:
    def __init__(self, mm):
        self.mm = mm
        self.info = None

        self.mode = MODE_MOTION

        self.cams = {}

    def start(self):
        for i, cam in enumerate(self.mm.sensor_mods["camera"].mans):
            cammover = CameraMover(cam, self)
            self.cams[cam.cam_name] = cammover

            thread_stream = threading.Thread(target=cammover.start)
            thread_stream.daemon = True
            thread_stream.start()

    def setmode(self, mode):
        self.mode = mode

        for cam in self.cams.values():
            cam.newmode = True

    def on_event(self, name, data):
        if name == "screen":
            img = data["image"]

            current_cam = self.mm.sensor_mods["camera"].mans[self.mm.sensor_mods["screen"].mode - 1].cam_name
            if current_cam in self.cams.keys():
                self.info = self.cams[current_cam].info

            if self.info is not None:
                if "center" in self.info:
                    cv2.putText(img, "x", (int(self.info["center"][0]), int(self.info["center"][1])),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

                    scale = 20
                    cv2.arrowedLine(img, (img.shape[1] // 2, img.shape[0] // 2),
                                    (img.shape[1] // 2 + int(self.info["move"][0] * self.info["speed"][0] * scale),
                                    img.shape[0] // 2 + int(self.info["move"][1] * self.info["speed"][1] * scale)), (0, 0, 255), 3)

                if "text" in self.info:
                    cv2.putText(img, self.info["text"], (10, 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

                #info = cv2.resize(bgr, (img.shape[1] // 2, img.shape[0] // 2))
                #img[:info.shape[0], :info.shape[1], :] = info


    def close(self):
        print("closing cameras")
        for cam in self.cams.values():
            print(cam.cam.cam_name)
            cam.controlcam(1, CAM_STOP, [0, 0])

        time.sleep(1)