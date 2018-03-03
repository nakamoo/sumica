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
from myutils import base64_decode_image

db = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)

def base64_encode_image(a):
    return base64.b64encode(a).decode("utf-8")
    
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
                k, data, callback = queue[0]

                outputs = [db.get(k+"-action"), db.get(k+"-pose"), db.get(k+"-object")]

                if None not in outputs:
                    redata = dict()
                    outputs = [json.loads(output.decode("utf-8")) for output in outputs]

                    redata["predictions"] = {"pose": outputs[1], "object": outputs[0]}

                    db.delete(k + "-action")
                    db.delete(k + "-pose")
                    db.delete(k + "-object")

                    data['predictions'] = redata['predictions']
                    db.rpush('master', json.dumps(data))

                    if data:
                        data['history'].append(('image_processed', time.time()))
                        redata['impath'] = data['impath']
                        redata['history'] = data['history']

                    redata = json.dumps(redata)

                    callback(redata)

                    del queue[0]
            except:
                traceback.print_exc()
                del queue[0]

                callback(None)

class HTTPHandler(tornado.web.RequestHandler):
    def post(self):
        file_body = self.request.files['image'][0]['body']
        image = Image.open(io.BytesIO(file_body))
        image = prepare_image(image)
        image = image.copy(order="C")

        k = str(uuid.uuid4())
        d = {"id": k, "image": base64_encode_image(image), "height": image.shape[0], "width": image.shape[1]}
        d = json.dumps(d)

        #db.rpush(settings.ACTION_QUEUE, d)
        db.rpush(settings.POSE_QUEUE, d)
        db.rpush(settings.OBJECT_QUEUE, d)

        done = [False]

        def send_message(redata):
            self.write(redata)
            print(redata)
            done[0] = True

        print("added", k, "to queue")
        queue.append([k, None, send_message])

        while not done[0]:
            time.sleep(0.01)

class SocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        print("WebSocket opened")

    def on_message(self, message):
        print("appending message")

        data = json.loads(message)
        data['history'].append(('server_received', time.time()))
        
        a = bytes(data["image"], encoding="utf-8")
        image = Image.open(io.BytesIO(base64.decodestring(a)))
        #image = Image.fromarray(base64_decode_image(data["image"], (data["width"], data["height"])))
        image = prepare_image(image)
        image = image.copy(order="C")

        k = str(uuid.uuid4())
        d = {"id": k, "image": base64_encode_image(image), "height": image.shape[0], "width": image.shape[1]}
        d = json.dumps(d)

        #db.rpush(settings.ACTION_QUEUE, d)
        db.rpush(settings.POSE_QUEUE, d)
        db.rpush(settings.OBJECT_QUEUE, d)

        def send_message(redata):
            if redata:
                self.write_message(redata)
        
        queue.append([k, data, send_message])

    def on_close(self):
        print("WebSocket closed")

def make_app():
    return tornado.web.Application([
        (r'/predict', HTTPHandler),
        (r'/predict_ws', SocketHandler)
    ])
#
if __name__ == "__main__":
    thread_stream = Thread(target=predict_loop)
    thread_stream.daemon = True
    thread_stream.start()
    
    print("* Starting web service...")
    app = make_app()
    app.listen(5002, address='0.0.0.0')
    tornado.ioloop.IOLoop.current().start()
