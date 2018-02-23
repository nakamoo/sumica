import cv2
import time
import requests
import numpy as np
import threading

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
        requests.get(
            self.cam.cam_addr + "/set_misc.cgi?loginuse=admin&loginpas={0}&ptz_patrol_rate={1}&ptz_patrol_up_rate={2}&ptz_patrol_down_rate={2}&ptz_patrol_left_rate={1}&ptz_patrol_right_rate={1}".format(
                self.cam.password, mag[0], mag[1]))
        requests.get(
            self.cam.cam_addr + "/decoder_control.cgi?loginuse=admin&loginpas={}&command={}&onestep={}".format(self.cam.password, cmd, onestep))

    def update(self):
        self.movecam()

    def movecam(self):
        onestep = 0
        cam = self.cam

        if self.man.mode == MODE_MOTION:
            if self.newmode:
                self.controlcam(onestep, CAM_CENTER, [10, 10])
                time.sleep(50)
                self.controlcam(onestep, CAM_STOP, [10, 10])

                self.newmode = False

            if len(self.cam.imdata) < 2:
                return

            #mask = cv2.absdiff(cam.imdata[-2]["smoothgray"], cam.imdata[-1]["smoothgray"])
            #mask = cv2.threshold(mask, 5, 255, cv2.THRESH_BINARY)[1]
            flow, flowmag, bgr = self.optflow(cam.imdata[-2]["bgr"], cam.imdata[-1]["bgr"])

            meanmag = np.mean(flowmag)

            cmd = CAM_STOP

            if meanmag > 1:
                M = cv2.moments(flowmag)
                cpX = int(M["m10"] / M["m00"])
                cpY = int(M["m01"] / M["m00"])

                moveX, moveY = 0, 0

                cX = cpX / flowmag.shape[1]
                cY = cpY / flowmag.shape[0]

                if cY < 0.5:
                    moveY = -1
                elif cY > 0.5:
                    moveY = 1

                if cX < 0.5:
                    moveX = -1
                elif cX > 0.5:
                    moveX = 1

                self.cammag = [int((0.5-cX)**2.0*20), int((0.5-cY)**2.0*20)]
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

                self.info = {"bgr": bgr, "magmap": flowmag, "mag": self.cammag, "center": [cpX, cpY], "move": [moveX, moveY]}
            else:
                self.info = {"bgr": bgr, "magmap": flowmag}

            #if time.time() - self.last_moved > 1:
            #    cmd = CAM_STOP

            if cmd != CAM_STOP:
                self.controlcam(onestep, cmd, self.cammag)
                time.sleep(1)
                self.controlcam(onestep, CAM_STOP, [0, 0])
                time.sleep(5)
            else:
                time.sleep(0.1)

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
        def camloop(cam):
            while True:
                if cam.cam_name not in self.cams:
                    self.cams[cam.cam_name] = CameraMover(cam, self)

                camman = self.cams[cam.cam_name]
                camman.update()

                time.sleep(0.1)

        for i, cam in enumerate(self.mm.sensor_mods["camera"].mans):
            thread_stream = threading.Thread(target=camloop, args=(cam,))
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
                bgr = cv2.cvtColor(self.info["magmap"], cv2.COLOR_GRAY2BGR)#self.info["bgr"]
                bgr /= np.max(bgr)
                bgr *= 255

                if "center" in self.info:
                    cv2.putText(bgr, "x", (self.info["center"][0], self.info["center"][1]),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    mag = self.info["mag"]
                    scale = 8
                    cv2.arrowedLine(bgr, (bgr.shape[1] // 2, bgr.shape[0] // 2),
                                    (bgr.shape[1] // 2 + int(self.info["move"][0] * mag[0] * scale),
                                    bgr.shape[0] // 2 + int(self.info["move"][1] * mag[1] * scale)), (0, 0, 255), 1)

                info = cv2.resize(bgr, (img.shape[1] // 2, img.shape[0] // 2))
                img[:info.shape[0], :info.shape[1], :] = info

                #cv2.putText(img, "{}".format(self.info["mag"]), (10, 60),
                #            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)


    def close(self):
        return