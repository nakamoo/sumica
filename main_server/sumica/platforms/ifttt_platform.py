import json
import re
import colorsys
import requests

from flask import Blueprint, request, jsonify, render_template

import controllermanager as cm

platform_name = "ifttt"
bp = Blueprint("ifttt_platform", __name__)

def data2command(data):
    command = {'platform': 'ifttt', 'data': {'url': data['urlText']}, 'stateful': False}

    return command

def execute(command):
    requests.post(command['url'], data={})

    return False

@bp.route('/parameters/' + platform_name)
def params():
    return render_template('ifttt-parameters.html')


@bp.route('/test/' + platform_name, methods=['POST'])
def test():
    args = request.get_json(force=True)
    command = data2command(args)

    cm.server_execute(args['username'], command)

    return 'ok', 200