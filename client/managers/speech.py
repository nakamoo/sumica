import time
import subprocess
from subprocess import Popen
import traceback
import requests
import coloredlogs, logging
coloredlogs.install(level="DEBUG")

import sys
sys.path.insert(0, "./")
sys.path.insert(0, "../../snowboy/examples/Python3")

from managers.hotword import snowboydecoder
import signal
import wave
import speech_recognition as sr
import utils.tts as tts

class Manager:
    def __init__(self, user, server_ip, speech_event):
        self.now_playing = None
        self.user = user
        self.ip = server_ip
        self.speech_event = speech_event

        self.speech_start = -1
        self.last_speech = -1
        self.listen_speech = False
        self.speech_detected = False
        self.current_buffer = bytearray(b'')

        models = ["hotwords/yes.pmdl", "hotwords/no.pmdl", "hotwords/ask.pmdl"]
        self.detector = snowboydecoder.HotwordDetector(models, sensitivity=[0.2, 0.5, 0.5], audio_gain=1)
        self.recognizer = sr.Recognizer()

    def start(self):
        #while True: << why loop?
        self.speech_event.wait()
        self.recognize()

    def interrupt_callback(self):
        if self.speech_event.is_set():
            return False
        else:
            logging.debug("SpeechManager: Interrupted")
            return True

    def speech(self, data, ans):
        if not self.listen_speech:
            if ans == 3:
                logging.debug("speech recognition: awake")
                tts.say("はい？")
                self.listen_speech = True
                self.listen_start = time.time()
                self.last_speech = time.time()
                self.speech_detected = False
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
            self.last_speech = time.time()

        listen_duration = time.time() - self.listen_start
        start_delay = 0.5
        max_duration = 5

        if self.listen_speech and listen_duration > start_delay:
            speech_over = time.time() - self.last_speech > 1

            if not speech_over and speech_duration < max_duration:
                self.current_buffer.extend(data)

                if ans == 0:
                    self.speech_detected = True

            else:
                if len(self.current_buffer) > 0:
                    sampwidth = self.detector.audio.get_sample_size(self.detector.audio.get_format_from_width(
                        self.detector.detector.BitsPerSample() / 8))

                    logging.debug("listening over")

                    if self.speech_detected:
                        try:
                            audiodata = sr.AudioData(current_buffer, detector.detector.SampleRate(), sampwidth)
                            text = self.recognizer.recognize_google(audiodata, language="ja")
                            print("You said: " + text)

                            data = {"user_name": self.user, "time": time.time(), "type": "speech", "text": text}
                            requests.post("%s/data/speech" % self.ip, data=data, verify=False)
                        except Exception as e:
                            tts.say("聞き取れませんでした")
                            print("some error")
                            print(e)
                    else:
                        logger.debug("no speech detected")
                        tts.say("何か言いましたか？")

                self.listen_speech = False
                self.current_buffer = bytearray(b'')

    def recognize(self):
        logging.debug("SpeechManager: Start")

        callbacks = [self.speech]

        try:
            self.detector.start(detected_callback=callbacks,
                           interrupt_check=self.interrupt_callback,
                           sleep_time=0.03)
        except Exception as e:
            logging.error("fatal audio error")
            logging.error(e)

        logging.debug("SpeechManager: Terminate")
        self.detector.terminate()

if __name__ == "__main__":
    import threading

    import utils

    SERVER_IP = "https://homeai.ml:{}".format(sys.argv[2])
    ID = sys.argv[1]

    man = Manager(ID, SERVER_IP)
    thread_stream = threading.Thread(target=man.start)
    thread_stream.daemon = False
    thread_stream.start()
