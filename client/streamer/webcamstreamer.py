import cv2
import threading
from streamer.streamdisplay import StreamDisplay
from streamer.streamer import Streamer


class WebcamStream(Streamer):
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        super().__init__()

    def start_stream(self, size=(640, 480)):
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, size[0]);
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, size[1]);

        while True:
            ret, frame = self.cap.read()
            self.image = frame

if __name__ == "__main__":
    stream = WebcamStream()
    stream.start_stream_threads()
    display = StreamDisplay(stream)
