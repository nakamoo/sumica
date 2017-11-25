import sys
sys.path.insert(0, "/Users/sean/projects/snowboy/examples/Python3")

import snowboydecoder

import signal
import wave

interrupted = False

def signal_handler(signal, frame):
    global interrupted
    interrupted = True

def interrupt_callback():
    global interrupted
    return interrupted

if len(sys.argv) == 1:
    print("Error: need to specify model name")
    print("Usage: python demo.py your.model")
    sys.exit(-1)

models = sys.argv[1:]
awake = 0
said_something = False
current_buffer = bytearray(b'')

signal.signal(signal.SIGINT, signal_handler)

import speech_recognition as sr
detector = snowboydecoder.HotwordDetector(models, sensitivity=[0.5]*len(models), audio_gain=3)
r = sr.Recognizer()
print('Listening... Press Ctrl+C to exit')

def speech(data, ans):
	#print(ans)
	global awake
	global current_buffer, said_something

	if ans == 3 and awake <= 0:
		print("awake")
		awake = 10
		said_something = False
	elif ans == -2:
		awake -= 1
	elif ans == 1:
		print("yes")
	elif ans == 2:
		print("no")
	
	if awake > 0:
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
					print("You said: " + r.recognize_google(audiodata, language="ja"))
				except Exception as e:
					print("some error")
					print(e)
			else:
				print("no speech detected")

		current_buffer = bytearray(b'')

callbacks = [speech]#[lambda: print("yes"),
             #lambda: print("no")]

detector.start(detected_callback=callbacks,
               interrupt_check=interrupt_callback,
               sleep_time=0.03)

detector.terminate()