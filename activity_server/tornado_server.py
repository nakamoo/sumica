import io
import uuid
import time
import base64
from threading import Thread
import json
import sys
import traceback

import tornado.ioloop
import tornado.web
import tornado.websocket

import redis
from PIL import Image
import numpy as np

import settings

db = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
model = None

PREDICT_QUEUE = "test"

def base64_encode_image(a):
    # base64 encode the input NumPy array
    return base64.b64encode(a).decode("utf-8")

def load_model():
    global model
    model = I3DModel()
    
def prepare_image(image):
    if image.mode != "RGB":
        image = image.convert("RGB")

    image = np.array(image)
    
    return image

queue = []

def predict_loop():
    while True:
        if len(queue) > 0:
            try:
                k, data, handler = queue[0]
                redata = dict()
                
                output = db.get(k)

                if output is not None:
                    redata["predictions"] = json.loads(output)
                    db.delete(k)

                    redata['impath'] = data['impath']
                    redata = json.dumps(redata)

                    print("sending back message")
                    handler.write_message(redata)

                    del queue[0]
            except:
                traceback.print_exc()
                del queue[0]
        
class SocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        print("WebSocket opened")

    def on_message(self, message):
        print("appending message")
        
        data = json.loads(message)
        
        a = bytes(data["image"], encoding="utf-8")
        image = Image.open(io.BytesIO(base64.decodestring(a)))
        image = prepare_image(image)
        image = image.copy(order="C")

        k = str(uuid.uuid4())
        d = {"id": k, "image": base64_encode_image(image), "height": image.shape[0], "width": image.shape[1]}
        db.rpush(settings.IMAGE_QUEUE, json.dumps(d))
        
        queue.append([k, data, self])

    def on_close(self):
        print("WebSocket closed")

def make_app():
    return tornado.web.Application([
        (r'/predict_ws', SocketHandler)
    ])

if __name__ == "__main__":
    thread_stream = Thread(target=predict_loop)
    thread_stream.daemon = True
    thread_stream.start()
    
    print("* Starting web service...")
    app = make_app()
    app.listen(5002)
    tornado.ioloop.IOLoop.current().start()
