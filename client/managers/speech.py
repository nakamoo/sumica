import time
import subprocess
from subprocess import Popen
import traceback
import requests
import logging

import sys
sys.path.insert(0, "./")
sys.path.insert(0, "../../snowboy/examples/Python3")

from managers.hotword import snowboydecoder
import signal
import wave
import speech_recognition as sr
import utils.tts as tts

class Manager:
    def __init__(self, user, server_ip):
        self.now_playing = None
        self.user = user
        self.ip = server_ip

    def start(self):
        interrupted = False

        def signal_handler(signal, frame):
            interrupted = True

        def interrupt_callback():
            return interrupted

        models = ["hotwords/yes.pmdl", "hotwords/no.pmdl", "hotwords/ask.pmdl"]
        listen_start = -1
        last_spoken = -1
        listening = False
        said_something = False
        current_buffer = bytearray(b'')

        #signal.signal(signal.SIGINT, signal_handler)
        
        detector = snowboydecoder.HotwordDetector(models, sensitivity=[0.2, 0.5, 0.5], audio_gain=1)
        r = sr.Recognizer()
        print('Listening... Press Ctrl+C to exit')

        def speech(data, ans):
            nonlocal last_spoken, listen_start, listening, current_buffer, said_something
            if not listening:
                if ans == 3:
                    print("speech recognition: awake")
                    tts.say("はい？")
                    listening = True
                    listen_start = time.time()
                    last_spoken = time.time()
                    said_something = False
                elif ans == 1:
                    logging.debug("speech indication: yes")

                    data = {"user_name": self.user, "time": time.time(), "type": "yes"}
                    
                    try:
                       requests.post("%s/data/speech" % self.ip, data=data, verify=False)
                    except:
                       logging.error("could not send speech event: yes")
                elif ans == 2:
                    logging.debug("speech indication: no")

                    data = {"user_name": self.user, "time": time.time(), "type": "no"}
                    
                    try:
                        requests.post("%s/data/speech" % self.ip, data=data, verify=False, timeout=1)
                    except:
                        logging.error("could not send speech event: no")
            elif ans == 0:
                 last_spoken = time.time()
           
            a = time.time() - listen_start
            if time.time() - last_spoken < 1 and a > 0.5 and a < 5:
                current_buffer.extend(data)
                if ans == 0:
                    said_something = True
            elif listening and a > 2:
                #print("buffer:", current_buffer)
                if len(current_buffer) > 0:
                    sampwidth = detector.audio.get_sample_size(detector.audio.get_format_from_width(
                        detector.detector.BitsPerSample() / 8))

                    print("listening over")

                    if said_something:
                        try:
                            audiodata = sr.AudioData(current_buffer, detector.detector.SampleRate(), sampwidth)
                            text = r.recognize_google(audiodata, language="ja")
                            print("You said: " + text)

                            data = {"user_name": self.user, "time": time.time(), "type": "speech", "text": text}
                            requests.post("%s/data/speech" % self.ip, data=data, verify=False)
                        except Exception as e:
                            tts.say("聞き取れませんでした")
                            print("some error")
                            print(e)
                    else:
                        print("no speech detected")
                        tts.say("何か言いましたか？")

                listening = False
                current_buffer = bytearray(b'')

        callbacks = [speech]#[lambda: print("yes"),
                     #lambda: print("no")]

        print("starting detector")

        try:
            detector.start(detected_callback=callbacks,
                       interrupt_check=interrupt_callback,
                       sleep_time=0.03)
        except Exception as e:
            logging.error("fatal audio error")
            logging.error(e)
            import sys
            sys.exit()

        detector.terminate()

if __name__ == "__main__":
    import threading

    import utils

    SERVER_IP = "https://homeai.ml:{}".format(sys.argv[2])
    ID = sys.argv[1]

    man = Manager(ID, SERVER_IP)
    thread_stream = threading.Thread(target=man.start) 
    thread_stream.daemon = False
    thread_stream.start()
