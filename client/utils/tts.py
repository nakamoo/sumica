import base64 
import json 
import requests 
import subprocess
import os
import wave, array

def make_stereo(file1, output):
    ifile = wave.open(file1)
    print(ifile.getparams())
    # (1, 2, 44100, 2013900, 'NONE', 'not compressed')
    (nchannels, sampwidth, framerate, nframes, comptype, compname) = ifile.getparams()
    assert comptype == 'NONE'  # Compressed not supported yet
    array_type = {1:'B', 2: 'h', 4: 'l'}[sampwidth]
    left_channel = array.array(array_type, ifile.readframes(nframes))[::nchannels]
    ifile.close()

    stereo = 2 * left_channel
    stereo[0::2] = stereo[1::2] = left_channel

    ofile = wave.open(output, 'wb')
    ofile.setparams((2, sampwidth, framerate, nframes, comptype, compname))
    ofile.writeframes(stereo.tostring())
    ofile.close()


def say(text):
    if not text:
        return

    path = "tts_cache/%s.wav" % text

    if os.path.exists(path):
        pass
    else:
        URL = "http://rospeex.nict.go.jp/nauth_json/jsServices/VoiceTraSS" 
  
        databody = {"method": "speak", 
                "params": ["1.1", 
                           {"language": "ja", "text": text, "voiceType": "F128", "audioType": "audio/x-wav"}]} 
        response = requests.post(URL, data=json.dumps(databody)) 
        tmp = json.loads(response.text) 
        wav = base64.decodestring(tmp["result"]["audio"].encode("utf-8")) 
        with open(path, "wb") as f: 
            f.write(wav)
        make_stereo(path, path)

    subprocess.Popen("aplay -Dplug:default %s" % path, shell=True)
