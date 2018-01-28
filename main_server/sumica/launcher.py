import importlib
import os
import sys
import json

import coloredlogs
import logging
from flask import Flask, request, jsonify, render_template
app = Flask(__name__)
app.config.from_object('config.Config')

logger = logging.getLogger(__name__)
coloredlogs.install(level=app.config['LOG_LEVEL'], logger=logger)

with app.app_context():
    import controllermanager as cm
    import sensors
    import interface
    from utils import log_command

sensor_mods = [sensors.chatbot_sensor, sensors.hue_sensor, sensors.image_sensor, sensors.speech_sensor]

for sensor in sensor_mods:
    app.register_blueprint(sensor.bp)

app.register_blueprint(interface.bp)

test_execute = []

@app.route('/controllers/execute', methods=['POST'])
def execute_controllers():
    user_id = request.form['user_name']
    response = []

    for controller in cm.cons[user_id].values():
        commands = controller.execute()
        for command in commands:
            response.append(command)
            if command:
                log_command(command, controller)

    if sum([len(r) for r in response]) > 0:
        logger.debug(response)

    response.extend(test_execute)
    test_execute.clear()

    return jsonify(response), 201

@app.route('/parameters/hue')
def hueoptions():
    return render_template('hue-options.html')

@app.route('/browser/hue', methods=['POST'])
def huetest():
    args = request.get_json(force=True)

    import re

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
    test_execute.append(state)

    return 'ok', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=app.config["PORT"],
            debug=app.config['DEBUG'], ssl_context=app.config['CONTEXT'], threaded=True)
