from streamer.webcamstreamer import WebcamStream
import cv2
import time
import requests
import sys
import numpy as np

def send(image, ip):
    cv2.imwrite("image.png", image)

    r = requests.post(ip, files={'image': open("image.png", "rb")})

    print("response: {}".format(r.text))

if __name__ == "__main__":
    if len(sys.argv) == 2:
        ip = sys.argv[1]
    else:
        ip = "http://localhost:5000/upload"

    print("ip", ip)

    stream = WebcamStream()
    stream.start_stream_threads()
    cv2.namedWindow("capture", cv2.WINDOW_NORMAL)
    last_img = None
    diff_thres = 0.5

    while (True):
        if stream.image is not None:
            skip = False

            frame = cv2.resize(stream.image, (500,500))
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
                cv2.imshow("capture", stream.image)
                last_img = gray
                k = cv2.waitKey(1)

                if k == 27:  # esc
                    break
                    
                try:
                    send(stream.image, ip)
                except:
                    print("unable to send image")
            else:
                print("%i: no frame data" % time.time())
        
        time.sleep(0.1)

    cv2.destroyAllWindows()
