from flask import Blueprint, request, jsonify, render_template

import controllermanager as cm

platform_name = "irkit"
bp = Blueprint("irkit_platform", __name__)

@bp.route('/parameters/' + platform_name)
def params():
    # TODO rename to hue-parameters.html
    return render_template('irkit-parameters.html')