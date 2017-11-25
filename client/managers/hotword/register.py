#!/usr/bin/env python3
# Requires PyAudio and PySpeech.
 
import speech_recognition as sr
import matplotlib.pyplot as plt
 
# Record Audio
r = sr.Recognizer()

with sr.Microphone() as source:
    r.adjust_for_ambient_noise(source)
    
    for i in range(3):
        print("Say something!")
        audio = r.listen(source)
        with open("%s.wav" % i, "wb") as f:
            f.write(audio.get_wav_data())