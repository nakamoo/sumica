import time
import logging
import _thread

import utils.tts as tts

from actors.actor import Actor

class VoiceActor(Actor):
    def __init__(self, user, ip):
        self.user = user
        self.ip = ip
        self.speaking_until = 0
        self.queue = []
        
        _thread.start_new_thread(self.talk_thread, ())
        
    def talk_thread(self):
        while True:
            if len(self.queue) > 0 and not self.speaking():
                text, callback = self.queue[0]
                del self.queue[0]
                duration = self._say(text)
                
                if callback:
                    def done():
                        time.sleep(max(0, duration - 1.0))
                        callback()

                    _thread.start_new_thread(done, ())
            
            time.sleep(0.1)

    def execute(self, act):
        if act['platform'] == "tts":
            self.add(act["data"])

    def speaking(self):
        return self.speaking_until >= time.time()
    
    def add(self, text, callback=None):
        self.queue.append([text, callback])
    
    def _say(self, text):
            duration = tts.tts_say(text)

            if duration >= 0:
                self.speaking_until = time.time() + duration
            else:
                self.speaking_until = time.time() + 0.5 * len(text)
                
            return duration