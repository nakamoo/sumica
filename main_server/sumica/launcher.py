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
    import platforms

    sensor_mods = [
        sensors.chatbot_sensor,
        sensors.hue_sensor,
        sensors.image_sensor,
        sensors.speech_sensor
    ]

    platform_mods = [
        platforms.hue_platform,
        platforms.voice_platform,
        platforms.ifttt_platform,
        platforms.alarm_platform,
        platforms.timetracker_platform
    ]
    platform_names = [p.platform_name for p in platform_mods]

    cm.initialize(platform_mods)

for sensor in sensor_mods:
    app.register_blueprint(sensor.bp)
for platform in platform_mods:
    app.register_blueprint(platform.bp)

app.register_blueprint(interface.bp)

@app.route('/platforms')
def get_platforms():
    return jsonify(platform_names), 200

@app.route('/controllers/execute', methods=['POST'])
def execute_controllers():
    username = request.form['user_name']
    commands = cm.client_execute(username)

    return jsonify(commands), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=app.config["PORT"],
            debug=app.config['DEBUG'], ssl_context=app.config['CONTEXT'], threaded=True)
