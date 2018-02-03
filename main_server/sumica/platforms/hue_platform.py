import json
import re
import colorsys

from flask import Blueprint, request, jsonify, render_template

import controllermanager as cm

platform_name = "hue"
bp = Blueprint("hue_platform", __name__)

def data2command(data):
    h = data['color'].lstrip('#')
    r, g, b = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)

    cmddata = list()

    if data['on']:
        hue = {"bri": int(v * 255), "hue": int(h * 65535), "sat": int(s * 255), 'on': True}
    else:
        hue = {'on': False}

    for id in data['hue_names'].split(','):
        cmddata.append({'id': id, 'state': hue})

    cmddata = json.dumps(cmddata)
    command = {'platform': 'hue', 'data': cmddata, 'stateful': True}

    if 'test' not in data:
        command['confirmation'] = '照明を変えますか？'

    return command

def execute(command):
    return True

@bp.route('/parameters/' + platform_name)
def params():
    return render_template('hue-parameters.html')


@bp.route('/test/' + platform_name, methods=['POST'])
def test():
    args = request.get_json(force=True)
    args["test"] = True
    command = data2command(args)
    cm.test_commands[args['username']].append(command)

    return 'ok', 200