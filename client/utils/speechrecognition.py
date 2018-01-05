import sys
sys.path.insert(0, "./")

import time
import speech_recognition as sr 
import utils.tts as tts

from managers.hotword import snowboydecoder

def listen_confirmation():
    confirmation_answer = None
    start_time = time.time()
    detected = False
    models = ["hotwords/yes.pmdl", "hotwords/no.pmdl"]
    detector = snowboydecoder.HotwordDetector(models, sensitivity=[0.5, 0.5], audio_gain=1)
    def interrupt_callback():
        nonlocal start_time, detected
        if detected:
            return True
        if time.time() - start_time > 5:
            return True
        else:
            return False
    def detected_callback(data, ans):
        nonlocal confirmation_answer, detected
        if ans == 1:
            confirmation_answer = True
            detected = True
        elif ans == 2:
            confirmation_answer = False
            detected = True

    detector.start(detected_callback=detected_callback, interrupt_check=interrupt_callback)
    return confirmation_answer

def confirm(confirmation):
    tts.say(confirmation)
    time.sleep(0.5)
    ans = listen_confirmation()
    if ans is None:
        tts.say("上手く聞こえませんでした,もう一度お願いします")
        ans = listen_confirmation()
    return ans

if __name__ == "__main__":
    print(confirm('確認です'))
