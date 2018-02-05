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
from controllers.nodes.alarm_node import AlarmNode
from controllers.nodes.ifttt_node import IFTTTNode

from controllers.nodes.timerange_node import TimeRangeNode
from controllers.nodes.input_smoother import InputSmootherNode
from controllers.nodes.voice_node import VoiceNode
from controllers.nodes.or_node import OrNode
from controllers.nodes.and_node import AndNode
from controllers.nodes.suppressor_node import SuppressorNode
from controllers.nodes.speech_node import SpeechNode

logger = logging.getLogger(__name__)
coloredlogs.install(level=current_app.config['LOG_LEVEL'], logger=logger)


class NodeManager(Controller):
    node_types = {
        'alarm': AlarmNode,
        'hue': HueNode,
        'timerange': TimeRangeNode,
        'inputsmoother': InputSmootherNode,
        'voice': VoiceNode,
        'timetracker': TimetrackerNode,
        'ifttt': IFTTTNode,
        'speech': SpeechNode,
        'or': OrNode,
        'and': AndNode
    }

    def __init__(self, username):
        super().__init__(username)

        self.nodes = []
        self.actions = []
        self.values = None

        self.update_nodes()

    def update_nodes(self):
        acts = list(db.actions.find())
        logger.debug("acts: " + str(acts))

        for r in acts:
            timerange = TimeRangeNode(self, r["data"])

            ornode = OrNode(None)
            ornode.inputs = r["data"]["inputs"]

            smoother = InputSmootherNode(self, r["data"])
            smoother.inputs = [ornode]

            andnode = AndNode(None)
            andnode.inputs = [smoother, timerange]

            self.nodes.append(timerange)
            self.nodes.append(ornode)
            self.nodes.append(smoother)
            self.nodes.append(andnode)

            if r["platform"] in self.node_types:
                print(r["platform"])
                act = NodeManager.node_types[r["platform"]](self, r["data"])
                act.inputs = [andnode]
                self.nodes.append(act)

            if r["platform"] == "timetracker":
                if r["data"]["lowText"]:
                    supnode = SuppressorNode(self, {"wait": int(r["data"]["repeat"])})
                    supnode.inputs = [(act, 0)]
                    self.nodes.append(supnode)
                    voicenode = VoiceNode(self, {"voiceText": r["data"]["lowText"]})
                    voicenode.inputs = [supnode]
                    self.nodes.append(voicenode)

                if r["data"]["highText"]:
                    supnode = SuppressorNode(self, {"wait": int(r["data"]["repeat"])})
                    supnode.inputs = [(act, 1)]
                    self.nodes.append(supnode)
                    voicenode = VoiceNode(self, {"voiceText": r["data"]["highText"]})
                    voicenode.inputs = [supnode]
                    self.nodes.append(voicenode)
            elif r["platform"] == "alarm":
                supnode = SuppressorNode(self, {"wait": int(r["data"]["repeat"])})
                supnode.inputs = [andnode]
                self.nodes.append(supnode)
                voicenode = VoiceNode(self, {"voiceText": r["data"]["sayText"]})
                voicenode.inputs = [supnode]
                self.nodes.append(voicenode)

        logger.debug("nodes: " + str(self.nodes))


    def on_event(self, event, data):
        if event == "activity":
            all_values = {}

            classes = cm.cons[self.username]["activitylearner"].classes

            for c in classes:
                all_values[c] = [False]

            logger.debug("graph inputs: {}".format(data))
            all_values[data] = [True]

            for node in self.nodes:
                values = []

                for inp in node.inputs:
                    if isinstance(inp, tuple):
                        values.append([all_values[inp[0]][inp[1]]])
                    else:
                        if inp in all_values:
                            values.append(all_values[inp])
                        else:
                            values.append([False])

                #logger.debug(str(node))
                #logger.debug(str(node.inputs))
                #logger.debug(str(values))
                all_values[node] = node.forward(values)
                #logger.debug(str(all_values[node]))
                #logger.debug("-"*10)

            #logger.debug("graph outputs: {}".format(all_values))
            self.values = all_values

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
