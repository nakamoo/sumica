import time
import traceback
import threading
import logging
import requests
import datetime

from managers.hotword import snowboydecoder
import speech_recognition as sr

from utils import tts
from managers import look

SPEAK = 0
LISTEN_HOTWORD = 1
LISTEN_SPEECH = 2

NO_SPEECH = -1

class Manager:
    def __init__(self, user, server_ip, mm):
        self.user = user
        self.ip = server_ip
        self.mm = mm
        self.mode = LISTEN_HOTWORD

        self.queue = []

        models = ["hotwords/yes.pmdl", "hotwords/no.pmdl", "hotwords/ask.pmdl"]
        self.detector = snowboydecoder.HotwordDetector(models, sensitivity=[0.5, 0.5, 0.4], audio_gain=1)
        self.recognizer = sr.Recognizer()

        self.sr_result = None

        self.run = True

        self.current_buffer = None
        self.speech_detected = False
        self.listen_start = 0
        self.last_speech = 0

    def start_sr(self):
        callbacks = [self.listen]

        try:
            logging.debug("starting voice detector...")
            self.detector.start(detected_callback=callbacks,
                                # interrupt_check=self.interrupt_callback,
                                sleep_time=0.03)
            logging.debug("started voice detector.")
        except Exception:
            traceback.print_exc()

        logging.debug("SpeechManager: Terminate")
        self.detector.terminate()

    def start(self):
        thread_stream = threading.Thread(target=self.start_sr)
        thread_stream.daemon = True
        thread_stream.start()

        while self.run:
            if len(self.queue) > 0:
                print(self.queue)

            if self.mode == LISTEN_SPEECH:
                while self.sr_result is None:
                    time.sleep(0.1)

                if self.sr_result != NO_SPEECH:
                    logging.debug("You said: " + self.sr_result)

                    # do something?
                    if "こんにちは" in self.sr_result:
                        self.queue.append(("tts", "こんにちは"))
                    elif "何時" in self.sr_result:
                        text = "今は"
                        now = datetime.datetime.now()
                        text += str(now.hour) + "時"
                        text += str(now.minute) + "分"
                        text += "です"
                        self.queue.append(("tts", text))
                    elif "プライベート" in self.sr_result:
                        if "解除" in self.sr_result:
                            self.queue.append(("tts", "プライベートモードを解除します"))
                            self.mm.sensor_mods["look"].setmode(look.MODE_MOTION)
                        else:
                            self.queue.append(("tts", "プライベートモードを始めます"))
                            self.mm.sensor_mods["look"].setmode(look.MODE_PRIVATE)

                self.sr_result = None

            if len(self.queue) > 0:
                cmd, data = self.queue[0]

                if cmd == "tts":
                    self.mode = SPEAK
                    d = tts.say(data)
                    time.sleep(d)
                elif cmd == "listen_speech":
                    self.current_buffer = bytearray(b'')
                    self.speech_detected = False
                    self.listen_start = time.time()
                    self.last_speech = time.time()

                    self.mode = LISTEN_SPEECH

                del self.queue[0]
            else:
                self.mode = LISTEN_HOTWORD

    def close(self):
        self.run = False
        self.detector.terminate()

    def listen(self, data, ans):
        if self.mode == LISTEN_HOTWORD:
            if ans == 3:
                logging.debug("speech recognition: awake")

                #self.queue.append(("tts", "はい？"))

                # write here for immediate listening
                self.current_buffer = bytearray(b'')
                self.mode = LISTEN_SPEECH
                self.queue.append(("listen_speech", None))
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
        elif self.mode == LISTEN_SPEECH and self.sr_result is None:
            if ans == 0:
                self.last_speech = time.time()

            listen_duration = time.time() - self.listen_start
            max_duration = 5
            #patience = 2 if self.speech_detected else 3
            patience = 0.5 if self.speech_detected else 3

            listen_speech = time.time() - self.last_speech < patience and listen_duration < max_duration

            if listen_speech:
                self.current_buffer.extend(data)
                logging.debug("recording speech...")

                if ans == 0:
                    self.speech_detected = True

            else:
                result = NO_SPEECH

                if len(self.current_buffer) > 0:
                    logging.debug("listening over; buffer length: {}".format(len(self.current_buffer)))

                    if self.speech_detected and len(self.current_buffer) > 0:
                        try:
                            sampwidth = self.detector.audio.get_sample_size(self.detector.audio.get_format_from_width(
                                self.detector.detector.BitsPerSample() / 8))
                            audiodata = sr.AudioData(self.current_buffer, self.detector.detector.SampleRate(),
                                                     sampwidth)
                            text = self.recognizer.recognize_google(audiodata, language="ja")

                            try:
                                data = {"user_name": self.user, "time": time.time(), "type": "speech", "text": text}
                                requests.post("%s/data/speech" % self.ip, data=data, verify=False)
                            except Exception:
                                #self.queue.append(("tts", "サーバとの通信がうまく行きませんでした"))
                                traceback.print_exc()
                            result = text

                        except sr.UnknownValueError:
                            self.queue.append(("tts", "何か言いましたでしょうか？"))
                            traceback.print_exc()
                        except Exception:
                            self.queue.append(("tts", "音声認識でエラーが出ました"))
                            traceback.print_exc()
                    else:
                        self.queue.append(("tts", "なにも聞こえませんでした"))

                self.sr_result = result
