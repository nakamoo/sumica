import json
import re
import colorsys

from flask import Blueprint, request, jsonify, render_template

import controllermanager as cm

platform_name = "voice"
bp = Blueprint("voice_platform", __name__)

def data2command(data):
    command = {'platform': 'tts', 'data': data['voiceText'], 'stateful': False}

    return command

def execute(data):
    return True

@bp.route('/parameters/' + platform_name)
def params():
    # TODO rename to hue-parameters.html
    return render_template('voice-parameters.html')


@bp.route('/test/' + platform_name, methods=['POST'])
def test():
    args = request.get_json(force=True)
    command = data2command(args)

    cm.test_commands[args['username']].append(command)

    return 'ok', 200