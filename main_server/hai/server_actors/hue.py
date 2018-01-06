import requests
import json
from flask import Flask

app = Flask(__name__)
app.config.from_pyfile(filename="../application.cfg")


colors = {
    '電球色': {"bri": 254, "hue": 14957, "sat": 141, 'on': True},
    '白色': {"bri": 254, "hue": 33016, "sat": 53, 'on': True},
    'オフ': {'on': False}
}


def format(hue_state):
    if hue_state["on"]:
        return hue_state
    else:
        return {"on": False}


def change_color(color, light=[1,2,3], confirm=False):
    c = colors[color]
    if isinstance(light, int):
        light = [light]
    data = []
    for l in light:
        data.append({'id': str(l), 'state': c})
    data = json.dumps(data)

    if confirm:
        re = [{'platform': 'hue', 'data': data, 'confirmation': "電気を" + color + "にしますか?"}]

    else:
        re = [{"platform": "tts", "data": "電気を" + color + "にします"},
          {'platform': 'hue', 'data': data}]

    return re

