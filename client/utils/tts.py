import base64 
import json 
import requests 
import subprocess

def say(text):      
    URL = "http://rospeex.nict.go.jp/nauth_json/jsServices/VoiceTraSS" 
  
    databody = {"method": "speak", 
                "params": ["1.1", 
                           {"language": "ja", "text": text, "voiceType": "F128", "audioType": "audio/x-wav"}]} 
    response = requests.post(URL, data=json.dumps(databody)) 
    tmp = json.loads(response.text) 
    wav = base64.decodestring(tmp["result"]["audio"].encode("utf-8")) 
    with open("out.wav", "wb") as f: 
        f.write(wav)
    subprocess.Popen("aplay out.wav", shell=True)
