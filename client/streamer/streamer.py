import threading


class Streamer(object):
    def __init__(self):
        self.image = None

    def start_stream(self):
        pass

    def start_stream_threads(self, url=None):
        if url is None:
            thread_stream = threading.Thread(target=self.start_stream)
        else:
            thread_stream = threading.Thread(target=self.start_stream, args=(url,))
        thread_stream.daemon = True
        thread_stream.start()

