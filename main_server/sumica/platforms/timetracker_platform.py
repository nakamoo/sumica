import json
import re
import colorsys

from flask import Blueprint, request, jsonify, render_template

import controllermanager as cm

platform_name = "timetracker"
bp = Blueprint("timetracker_platform", __name__)


def execute(data):
    return True

@bp.route('/parameters/' + platform_name)
def params():
    # TODO rename to hue-parameters.html
    return render_template('timetracker-parameters.html')


@bp.route('/test/' + platform_name, methods=['POST'])
def test():
    return 'ok', 200