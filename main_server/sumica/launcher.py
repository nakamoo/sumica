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

    sensor_mods = [
        sensors.chatbot_sensor,
        sensors.hue_sensor,
        sensors.image_sensor,
        sensors.speech_sensor
    ]

    cm.initialize()

for sensor in sensor_mods:
    app.register_blueprint(sensor.bp)

app.register_blueprint(interface.bp)

@app.route('/controllers/execute', methods=['POST'])
def execute_controllers():
    username = request.form['user_name']
    commands = cm.client_execute(username)

    return jsonify(commands), 201

@app.route('/node_types')
def get_node_types():
    types = cm.get_node_types()

    return jsonify(types), 200

@app.route('/test_execute', methods=['POST'])
def test_execute():
    args = request.get_json(force=True)
    logger.debug(str(args))
    cm.test_execute(args)

    return "ok", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=app.config["PORT"],
            debug=app.config['DEBUG'], ssl_context=app.config['CONTEXT'], threaded=True)
