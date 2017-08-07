import cv2
import threading
import time

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
                        send(stream.image, self.server_ip)
                    except:
                        print("unable to send image to server.")
            
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

        r = requests.post(ip, files={'image': open("image.png", "rb")})

        print("response: {}".format(r.text))