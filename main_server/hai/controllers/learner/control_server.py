import flask
from nn import action_nn
import json
import hello

from flask import Flask, render_template, request
app = Flask(__name__)

#actor = action_nn.NNActor()

@app.route('/rebuild', methods=["POST"])
def rebuild():
    actor.rebuild()

    return "ok"

@app.route('/control', methods=["POST"])
def control():
    state = request.get_json()["state"]
    
    act = []

    #actor.act(act, state)
    hello.act(act, state)

    if act is None:
        return "null"
    else:
        return json.dumps(act)

if __name__ == "__main__":
    app.run(host='localhost', threaded=False, use_reloader=False, debug=True, port=5003)