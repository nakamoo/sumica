import base64 
import json 
import requests 
import subprocess
import os

def say(text):
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
    subprocess.Popen("aplay %s" % path, shell=True)
