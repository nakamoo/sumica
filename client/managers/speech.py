import time
import subprocess
from subprocess import Popen
import traceback
import requests

import sys
sys.path.insert(0, "./")
sys.path.insert(0, "../../snowboy/examples/Python3")

from managers.hotword import snowboydecoder
import signal
import wave
import speech_recognition as sr

class Manager:
    def __init__(self, user, server_ip, actions):
        self.now_playing = None
        self.user = user
        self.ip = server_ip
        self.actions = actions

    def start(self):
        interrupted = False

        def signal_handler(signal, frame):
            interrupted = True

        def interrupt_callback():
            return interrupted

        models = ["hotwords/yes.pmdl", "hotwords/no.pmdl", "hotwords/ask.pmdl"]
        awake = 0
        said_something = False
        current_buffer = bytearray(b'')

        #signal.signal(signal.SIGINT, signal_handler)
        
        detector = snowboydecoder.HotwordDetector(models, sensitivity=[0.5]*len(models), audio_gain=1)
        r = sr.Recognizer()
        print('Listening... Press Ctrl+C to exit')

        def speech(data, ans):
            nonlocal awake, current_buffer, said_something

            if awake <= 0:
                if ans == 3:
                    print("speech recognition: awake")
                    self.actions.act("tts", "はい？")
                    awake = 20
                    said_something = False
                elif ans == 1:
                    print("speech indication: yes")

                    data = {"user_name": self.user, "time": time.time(), "type": "yes"}
                    requests.post("%s/data/speech" % self.ip, data=data, verify=False)
                elif ans == 2:
                    print("speech indication: no")

                    data = {"user_name": self.user, "time": time.time(), "type": "no"}
                    requests.post("%s/data/speech" % self.ip, data=data, verify=False)
            elif ans == -2:
                awake -= 1
            
            if awake > 0 and awake <= 15:
                current_buffer.extend(data)
                if ans == 0:
                    said_something = True
            else:
                if len(current_buffer) > 0:
                    sampwidth = detector.audio.get_sample_size(detector.audio.get_format_from_width(
                        detector.detector.BitsPerSample() / 8))

                    """
                    waveFile = wave.open("speech.wav", 'wb')
                    waveFile.setnchannels(detector.detector.NumChannels())
                    waveFile.setsampwidth(detector.audio.get_sample_size(detector.audio.get_format_from_width(
                        detector.detector.BitsPerSample() / 8)))
                    waveFile.setframerate(detector.detector.SampleRate())
                    waveFile.writeframes(current_buffer)
                    waveFile.close()
                    """
                    print("over")

                    if said_something:
                        try:
                            audiodata = sr.AudioData(current_buffer, detector.detector.SampleRate(), sampwidth)
                            text = r.recognize_google(audiodata, language="ja")
                            print("You said: " + text)

                            data = {"user_name": self.user, "time": time.time(), "type": "speech", "text": text}
                            requests.post("%s/data/speech" % self.ip, data=data, verify=False)
                        except Exception as e:
                            self.actions.act("tts", "聞き取れませんでした")
                            print("some error")
                            print(e)
                    else:
                        print("no speech detected")
                        self.actions.act("tts", "聞き取れませんでした")

                current_buffer = bytearray(b'')

        callbacks = [speech]#[lambda: print("yes"),
                     #lambda: print("no")]

        print("starting detector")
        detector.start(detected_callback=callbacks,
                       interrupt_check=interrupt_callback,
                       sleep_time=0.03)

        detector.terminate()

if __name__ == "__main__":
    import threading

    import utils
    from utils.actions import Actions

    SERVER_IP = "https://homeai.ml:{}".format(sys.argv[2])
    ID = sys.argv[1]

    man = Manager(ID, SERVER_IP, Actions())
    thread_stream = threading.Thread(target=man.start) 
    thread_stream.daemon = False
    thread_stream.start()
