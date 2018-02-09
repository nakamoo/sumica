import time

from flask import current_app
import numpy as np
import coloredlogs
import logging

from .node import Node
import controllermanager as cm

from controllers.nodes.voice_node import VoiceNode
from controllers.nodes.suppressor_node import SuppressorNode

logger = logging.getLogger(__name__)
coloredlogs.install(level=current_app.config['LOG_LEVEL'], logger=logger)

class AlarmNode(Node):
    param_file = 'alarm-parameters.html'
    display_name = "Alarm"
    input_types = ["boolean"]
    output_types = ["action"]
    icon = Node.icon_pic("fa fa-bell")

    def __init__(self, id, man, args):
        super().__init__(id, args)

        repeat = int(args["repeat"])
        supnode = SuppressorNode(uuid.uuid4(), man, {"wait": repeat})
        supnode.inputs = [[{"id": id, "index": 0}]]
        man.nodes.append(supnode)
        voicenode = VoiceNode(uuid.uuid4(), man, {"voiceText": args["sayText"]})
        voicenode.inputs = [[{"id": supnode.id, "index": 0}]]
        man.nodes.append(voicenode)

    def forward(self, values):
        # identity
        return values
