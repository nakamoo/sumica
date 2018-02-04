import time
from datetime import datetime

from flask import current_app
from .controller import Controller
from utils import db
import coloredlogs
import logging

import controllermanager as cm

from controllers.nodes.hue_node import HueNode
from controllers.nodes.timetracker_node import TimetrackerNode

from controllers.nodes.timerange_node import TimeRangeNode
from controllers.nodes.input_smoother import InputSmootherNode
from controllers.nodes.voice_node import VoiceNode
from controllers.nodes.or_node import OrNode
from controllers.nodes.and_node import AndNode

logger = logging.getLogger(__name__)
coloredlogs.install(level=current_app.config['LOG_LEVEL'], logger=logger)


class NodeManager(Controller):
    def __init__(self, username):
        super().__init__(username)

        self.node_types = {
            'hue': HueNode,
            'timerange': TimeRangeNode,
            'inputsmoother': InputSmootherNode,
            'voice': VoiceNode,
            'timetracker': TimetrackerNode
        }

        self.nodes = []
        self.actions = []

        self.update_nodes()

    def update_nodes(self):
        acts = list(db.actions.find())
        logger.debug("acts: " + str(acts))

        for r in acts:
            timerange = TimeRangeNode(r["data"])

            ornode = OrNode(None)
            ornode.inputs = r["data"]["inputs"]

            smoother = InputSmootherNode(r["data"])
            smoother.inputs = [ornode]

            andnode = AndNode(None)
            andnode.inputs = [smoother, timerange]

            act = self.node_types[r["platform"]](r["data"])
            act.inputs = [andnode]

            self.nodes.append(timerange)
            self.nodes.append(ornode)
            self.nodes.append(smoother)
            self.nodes.append(andnode)
            self.nodes.append(act)

        logger.debug("nodes: " + str(self.nodes))


    def on_event(self, event, data):
        if event == "activity":
            all_values = {}

            classes = cm.cons[self.username]["activitylearner"].classes

            for c in classes:
                all_values[c] = [False]

            all_values[data] = [True]

            for node in self.nodes:
                values = [all_values[inp] for inp in node.inputs]
                #logger.debug(str(node))
                #logger.debug(str(node.inputs))
                #logger.debug(str(values))
                all_values[node] = node.forward(values)
                #logger.debug(str(all_values[node]))
                #logger.debug("-"*10)

            actions = []

            for key, val in all_values.items():
                for element in val:
                    if isinstance(element, dict) and "platform" in element:
                        actions.append(element)

            self.actions = actions


    def execute(self):
        actions = self.actions
        self.actions = []
        return actions
