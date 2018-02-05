import time

from flask import current_app
import numpy as np
import coloredlogs
import logging

from .node import Node
import controllermanager as cm

logger = logging.getLogger(__name__)
coloredlogs.install(level=current_app.config['LOG_LEVEL'], logger=logger)

class AlarmNode(Node):
    param_file = 'alarm-parameters.html'
    display_name = "Alarm"
    input_types = ["boolean"]
    output_types = ["action"]

    def __init__(self, man, args):
        super().__init__(args)