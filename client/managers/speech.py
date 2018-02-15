# -*- encoding: utf-8 -*-

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

        self.listen_start = -1
        self.last_speech = -1
        self.listen_speech = False
        self.speech_detected = False
        self.current_buffer = bytearray(b'')
        self.ignore_time = 0

        models = ["hotwords/yes.pmdl", "hotwords/no.pmdl", "hotwords/ask.pmdl"]
        self.detector = snowboydecoder.HotwordDetector(models, sensitivity=[0.2, 0.5, 0.5], audio_gain=2)
        self.recognizer = sr.Recognizer()

    def start(self):
        #while True: << why loop?
        #self.speech_event.wait()
        self.recognize()

    def interrupt_callback(self):
        if self.speech_event.is_set():
            return False
        else:
            logging.debug("SpeechManager: Interrupted")
            return True

    def speech(self, data, ans):
        if time.time() >= self.ignore_time:
            #logging.debug(ans)
            
            if not self.listen_speech:
                if ans == 3:
                    logging.debug("speech recognition: awake")
                    tts.say("はい？")
                    self.listen_speech = True
                    self.speech_detected = False
                    
                    hai_len = 1.5
                    self.listen_start = time.time() + hai_len
                    self.last_speech = time.time() + hai_len
                    self.ignore_time = time.time() + hai_len
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
        else:
            logging.debug("ignoring...")
            return

        listen_duration = time.time() - self.listen_start
        max_duration = 5
        patience = 2 if self.speech_detected else 3

        if self.listen_speech:
            speech_over = time.time() - self.last_speech > patience

            if not speech_over and listen_duration < max_duration:
                self.current_buffer.extend(data)
                logging.debug("recording speech...")

                if ans == 0:
                    self.speech_detected = True

            else:
                if len(self.current_buffer) > 0:
                    sampwidth = self.detector.audio.get_sample_size(self.detector.audio.get_format_from_width(
                        self.detector.detector.BitsPerSample() / 8))

                    logging.debug("listening over; buffer length: {}".format(len(self.current_buffer)))

                    if self.speech_detected and len(self.current_buffer) > 0:
                        #if len(self.current_buffer) > 0:
                        try:
                            audiodata = sr.AudioData(self.current_buffer, self.detector.detector.SampleRate(), sampwidth)
                            text = self.recognizer.recognize_google(audiodata, language="ja")
                            logging.debug("You said: " + text)
                            try:
                                data = {"user_name": self.user, "time": time.time(), "type": "speech", "text": text}
                                requests.post("%s/data/speech" % self.ip, data=data, verify=False)
                            except Exception as e:
                                self.ignore_time = time.time() + 1
                                tts.say("サーバとの通信がうまく行きませんでした")
                                traceback.print_exc()
                        except sr.UnknownValueError:
                            self.ignore_time = time.time() + 3
                            tts.say("何か言いましたか？")
                        except Exception as e:
                            self.ignore_time = time.time() + 1
                            tts.say("音声認識ができませんでした")
                            traceback.print_exc()
                    else:
                        self.ignore_time = time.time() + 3
                        logging.debug("no speech detected")
                        tts.say("聞こえませんでした")

                self.listen_speech = False
                self.current_buffer = bytearray(b'')

    def recognize(self):
        logging.debug("SpeechManager: Start")

        callbacks = [self.speech]

        try:
            logging.debug("starting voice detector...")
            self.detector.start(detected_callback=callbacks,
                           #interrupt_check=self.interrupt_callback,
                           sleep_time=0.03)
            logging.debug("started voice detector.")
        except Exception as e:
            logging.error("fatal audio error")
            logging.error(e)

        logging.debug("SpeechManager: Terminate")
        self.detector.terminate()

    def close(self):
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
