import json
import re

from flask import Blueprint, request, jsonify, render_template

import controllermanager as cm

platform_name = "hue"
bp = Blueprint("hue_platform", __name__)

@bp.route('/parameters/' + platform_name)
def params():
    # TODO rename to hue-parameters.html
    return render_template('hue-parameters.html')

@bp.route('/test/' + platform_name, methods=['POST'])
def test():
    args = request.get_json(force=True)

    search = re.search('hsv\((\d*),\s(\d*)%,\s(\d*)%\)', args['color'])

    if search:
        h = int(search.group(1))
        s = int(search.group(2))
        v = int(search.group(3))
    else:
        return 'data error', 400

    data = list()

    if args['on']:
        hue = {"bri": int(v/100*255), "hue": int(h/360*65535), "sat": int(s/100*255), 'on': True}
    else:
        hue = {'on': False}

    for id in args['names'].split(','):
        data.append({'id': id, 'state': hue})

    data = json.dumps(data)
    state = [{'platform': 'hue', 'data': data}]
    cm.test_execute[args['username']].append(state)

    return 'ok', 200