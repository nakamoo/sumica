import time
from datetime import datetime
from collections import OrderedDict
import uuid

from flask import current_app
from .controller import Controller
from utils import db
import coloredlogs
import logging
from toposort import toposort, toposort_flatten

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


def topo_sort(nodes):
    n = [node.id for node in nodes]
    n_dict = dict()

    if None in n:
        logger.error("node with id None")

    for i, node in enumerate(nodes):
        dep = []

        for arg in node.inputs:
            for val in arg:
                if val["id"] in n:
                    dep.append(n.index(val["id"]))

        n_dict[i] = set(dep)

    sorted_nodes = list(toposort(n_dict))

    re = []
    for rank in sorted_nodes:
        for i in list(rank):
            re.append(nodes[i])

    return re

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

        self.nodes = OrderedDict([])
        self.actions = []
        self.values = None

        self.update_nodes()

    def update_nodes(self):
        nodes = []

        acts = list(db.actions.find())
        logger.debug("acts: " + str(acts))

        for r in acts:
            if "action" in NodeManager.node_types[r["platform"]].output_types:
                timerange = TimeRangeNode(self, r["data"])
                timerange.id = uuid.uuid4()

                #ornode = OrNode(self, None)
                #ornode.id = uuid.uuid4()
                #ornode.inputs = r["data"]["inputs"]

                smoother = InputSmootherNode(self, r["data"])
                smoother.id = uuid.uuid4()
                smoother.inputs = r["data"]["inputs"]#[[{"index": 0, "id": ornode.id}]]

                andnode = AndNode(self, None)
                andnode.id = uuid.uuid4()
                andnode.inputs = [[{"index": 0, "id": smoother.id}], [{"index": 0, "id": timerange.id}]]

                nodes.append(timerange)
                #nodes.append(ornode)
                nodes.append(smoother)
                nodes.append(andnode)

                act = NodeManager.node_types[r["platform"]](self, r["data"])
                act.inputs = [[{"index":0, "id": andnode.id}]]
                act.id = str(r["_id"])
                nodes.append(act)

                if r["platform"] == "timetracker":
                    if r["data"]["lowText"]:
                        supnode = SuppressorNode(self, {"wait": int(r["data"]["repeat"])})
                        supnode.id = uuid.uuid4()
                        supnode.inputs = [[{"id": act.id, index: 0}]]
                        nodes.append(supnode)
                        voicenode = VoiceNode(self, {"voiceText": r["data"]["lowText"]})
                        voicenode.inputs = [[{"id": supnode.id, index: 0}]]
                        nodes.append(voicenode)

                    if r["data"]["highText"]:
                        supnode = SuppressorNode(self, {"wait": int(r["data"]["repeat"])})
                        supnode.id = uuid.uuid4()
                        supnode.inputs = [[{"id": act.id, index: 1}]]
                        nodes.append(supnode)
                        voicenode = VoiceNode(self, {"voiceText": r["data"]["highText"]})
                        voicenode.id = uuid.uuid4()
                        voicenode.inputs = [[{"id": supnode.id, index: 0}]]
                        nodes.append(voicenode)
                elif r["platform"] == "alarm":
                    repeat = 10

                    try:
                        repeat = int(r["data"]["repeat"])
                    except:
                        pass

                    supnode = SuppressorNode(self, {"wait": repeat})
                    supnode.id = uuid.uuid4()
                    supnode.inputs = [[{"id": act.id, "index": 0}]]
                    nodes.append(supnode)
                    voicenode = VoiceNode(self, {"voiceText": r["data"]["sayText"]})
                    voicenode.id = uuid.uuid4()
                    voicenode.inputs = [[{"id": supnode.id, "index": 0}]]
                    nodes.append(voicenode)
            else:
                act = NodeManager.node_types[r["platform"]](self, r["data"])
                act.inputs = r["data"]["inputs"]
                act.id = str(r["_id"])
                nodes.append(act)


        nodes = topo_sort(nodes)
        self.nodes = OrderedDict([(n.id, n) for n in nodes])

        logger.debug("nodes: " + str(self.nodes))


    def on_event(self, event, data):
        if event == "activity":
            all_values = {}

            classes = cm.cons[self.username]["activitylearner"].classes

            for c in classes:
                all_values[c] = [False]

            logger.debug("graph inputs: {}".format(data))
            all_values[data] = [True]

            for node_id, node in self.nodes.items():
                all_args = []

                print(node, node_id)

                for arg in node.inputs:
                    arg_val = []

                    for source in arg:
                        arg_val.append(all_values[source["id"]][source["index"]])

                    #logger.debug(str(arg_val))
                    # OR operation
                    all_args.append(True in arg_val)

                #logger.debug(str(node) + " " + str(node_id))
                #logger.debug(str(node.inputs))
                #logger.debug(str(all_args))
                all_values[node_id] = node.forward(all_args)
                #logger.debug(str(all_values[node_id]))
                #logger.debug("-"*10)

            logger.debug("graph outputs: {}".format(all_values))
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
