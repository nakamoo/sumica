from flask import Flask, render_template, request, jsonify
import json
import requests
import uuid
import os
import importlib
from database import mongo

fs = ['sensors.{}'.format(f[:-3]) for f in os.listdir('sensors') if f.endswith('.py')]
sensor_mods = map(importlib.import_module, fs)

fs = ['controllers.{}'.format(f[:-3]) for f in os.listdir('controllers') if f.endswith('.py')]
control_mods = []
for f in fs:
  try:
    m = importlib.import_module(f)
    if "on_global_event" in dir(m):
      control_mods.append(m)
  except:
    print("failed to load", f)

from controllers.controller import Sample
from controllers.detection import Detection
from controllers.chatbot import Chatbot
from controllers.hello import HelloController

app = Flask(__name__)
app.config.from_pyfile(filename="application.cfg")

def standard_controllers(user_name):
    return [Sample(), Detection(), Chatbot(), HelloController(user_name)]

# TODO: use DB
controllers_objects = {}
controllers_objects['koki'] = standard_controllers('koki')
controllers_objects['sean'] = standard_controllers('sean')

@app.route('/')
def home_page():
    return render_template('index.html')


def trigger_controllers(user, event, data):
    if user is None:
        for c in control_mods:
            c.on_global_event(event, data)
    else:
        for c in controllers_objects[user]:
            c.on_event(event, data)

for sensor in sensor_mods:
    app.register_blueprint(sensor.app)


@app.route('/controllers')
def get_controllers():
    return "Not implemented", 404


@app.route('/controllers/update', methods=['POST'])
def update_controllers():
    return "Not implemented", 404


@app.route('/controllers/execute', methods=['POST'])
def execute_controllers():
    user_id = request.form['user_name']
    response = {}

    for controller in controllers_objects[user_id]:
        commands = controller.execute()
        for device, command in commands.items():
            response[device] = command

    return jsonify(response), 201


@app.route('/controllers/<controller_name>/execute', methods=['POST'])
def execute_specific_controller():
    return "Not implemented", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
