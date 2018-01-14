import importlib
import os
import sys

from flask import Flask, request, jsonify

app = Flask(__name__)
app.config.from_object('config.Config')

with app.app_context():
    import controllermanager as cm
    import sensors
    import interface

sensor_mods = [sensors.chatbot_sensor, sensors.hue_sensor, sensors.image_sensor, sensors.speech_sensor]

for sensor in sensor_mods:
    app.register_blueprint(sensor.bp)

app.register_blueprint(interface.bp)

@app.route('/controllers/execute', methods=['POST'])
def execute_controllers():
    user_id = request.form['user_name']
    response = []

    for controller in cm.cons[user_id].values():
        commands = controller.execute()
        for command in commands:
            response.append(command)

    return jsonify(response), 201


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=app.config["PORT"],
            debug=app.config['DEBUG'], ssl_context=app.config['CONTEXT'], threaded=True)
