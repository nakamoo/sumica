import zerorpc
import imageparser
import imagedb
import os

CLEAR_IMGS = True
image_dir = "../hai_server2/images"

class HelloRPC(object):
    def newimage(self, path):
        print("new image: {}".format(path))

        # image processing code goes here
        mean = imageparser.mean(path)
        imagedb.save(path, mean)

        if CLEAR_IMGS:
            os.remove(path)

        return "ok"#str(mean)

if CLEAR_IMGS:
    print("deleting {} images".format(len(os.listdir(image_dir))))
    for f in os.listdir(image_dir):
        os.remove(os.path.join(image_dir, f))

s = zerorpc.Server(HelloRPC())
s.bind("tcp://0.0.0.0:5001")
s.run()