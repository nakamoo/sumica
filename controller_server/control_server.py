import flask
from nn import action_nn
import json

from flask import Flask, render_template, request
app = Flask(__name__)

actor = action_nn.NNActor()

@app.route('/rebuild', methods=["POST"])
def rebuild():
    actor.rebuild()

    return "ok"

@app.route('/control', methods=["POST"])
def control():
    print(request.get_json())
    act = actor.act(request.get_json()["state"])

    print("act", act)

    if act is None:
        return "null"
    else:
        return json.dumps({"app": act[0], "cmd": act[1]})

if __name__ == "__main__":
    app.run(host='localhost', threaded=False, use_reloader=False, debug=True, port=5003)