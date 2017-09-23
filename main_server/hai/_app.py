from flask import Flask
import importlib
import os
app = Flask(__name__)
app.config.from_pyfile(filename="application.cfg")

# load sensor modules as blueprints
fs = ['sensors.{}'.format(f[:-3]) for f in os.listdir('sensors') if f.endswith('.py')]
sensor_mods = map(importlib.import_module, fs)

for sensor in sensor_mods:
    app.register_blueprint(sensor.bp)
