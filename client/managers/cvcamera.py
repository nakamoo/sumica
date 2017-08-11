import requests
import cv2
import threading
import time
import json
import colorsys

def visualize(frame, all_boxes, win_name="frame"):
    for result in all_boxes:
        det = result["box"]
        name = result["label"]

        i = sum([ord(x) for x in name])
        c = colorsys.hsv_to_rgb(i%100.0/100.0, 1.0, 0.9)
        c = tuple([int(x * 255.0) for x in c])
        cv2.putText(frame, name, (det[0], det[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, c, 2)
        cv2.rectangle(frame, (det[0], det[1]), (int(det[2]), int(det[3])), c, 2)

class Manager:
    def __init__(self, server_ip):
        self.server_ip = server_ip
        self.enabled = True

        try:
            self.cap = cv2.VideoCapture(0)
            print("webcam detected.")
        except:
            print("no webcam detected.")
            self.enabled = False

        self.image = None

    def capture_loop(self):
        while True:
            ret, frame = self.cap.read()

            if not ret:
                self.enabled = False

            self.image = frame

    def start(self):
        if not self.enabled:
            return

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640);
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480);

        thread_stream = threading.Thread(target=self.capture_loop)
        thread_stream.daemon = True
        thread_stream.start()
   
        cv2.namedWindow("capture", cv2.WINDOW_NORMAL)
        last_img = None
        diff_thres = 0.5

        while True:
            if self.image is not None:
                skip = False

                frame = cv2.resize(self.image, (500, 500))
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.GaussianBlur(gray, (21, 21), 0)

                if last_img is None:
                    last_img = gray

                frameDelta = cv2.absdiff(last_img, gray)
                thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
                #cv2.imshow("diff", thresh)

                #if np.sum(thresh) <= 0:
                #    skip = True
                
                if not skip:
                    cv2.imshow("capture", self.image)
                    last_img = gray
                    k = cv2.waitKey(1)

                    if k == 27:
                        break
                        
                    try:
                        self.send(self.image, self.server_ip)
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

    def send(self, image, ip):
        cv2.imwrite("image.png", image)
        
        r = requests.post("{}/detect".format(ip), files={'image': open("image.png", "rb")})

        print("response: {}".format(r.text))

        visualize(image, json.loads(r.text))
        cv2.imshow("dets", image)
        cv2.waitKey(1)
