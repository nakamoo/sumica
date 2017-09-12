from _app import app
from flask import Flask, render_template, request, jsonify
import json
import requests
import uuid
import os
import importlib
from database import mongo, controllers_objects
import sys


port = sys.argv[1]

# load sensor modules as blueprints
fs = ['sensors.{}'.format(f[:-3]) for f in os.listdir('sensors') if f.endswith('.py')]
sensor_mods = map(importlib.import_module, fs)

for sensor in sensor_mods:
    app.register_blueprint(sensor.bp)

@app.route('/')
def home_page():
    return render_template('index.html')

@app.route('/controllers')
def get_controllers():
    return "Not implemented", 404


@app.route('/controllers/update', methods=['POST'])
def update_controllers():
    return "Not implemented", 404


@app.route('/controllers/execute', methods=['POST'])
def execute_controllers():
    user_id = request.form['user_name']
    response = []

    for controller in controllers_objects[user_id]:
        commands = controller.execute()
        for command in commands:
            response.append(command)

    return jsonify(response), 201


@app.route('/controllers/<controller_name>/execute', methods=['POST'])
def execute_specific_controller():
    return "Not implemented", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(port),
            debug=app.config['DEBUG'], ssl_context=app.config['CONTEXT'], threaded=True)
