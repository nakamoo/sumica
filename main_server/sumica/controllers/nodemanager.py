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
from controllers.nodes.not_node import NotNode
from controllers.nodes.delay_node import DelayNode
from controllers.nodes.suppressor_node import SuppressorNode
from controllers.nodes.speech_node import SpeechNode
from controllers.nodes.change_node import ChangeNode
from controllers.nodes.memory_node import MemoryNode
#from controllers.nodes.acttracker_node import ActTrackerNode

logger = logging.getLogger(__name__)
coloredlogs.install(level=current_app.config['LOG_LEVEL'], logger=logger)


def compare_states(nodes, old_state, new_state):
    if old_state is None:
        return [], []

    changed_manuals, changed_actions = [], []

    for nid, old_val in old_state.items():
        if nid in nodes and nid in new_state and new_state[nid] != old_val:
            # dirty
            if nodes[nid].display_name == "Speech Recognition":
                changed_manuals.append(nid)
            elif "action" in nodes[nid].output_types:
                changed_actions.append(nid)

    return changed_manuals, changed_actions

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
        #'alarm': AlarmNode,
        'speech': SpeechNode,
        'timerange': TimeRangeNode,

        'voice': VoiceNode,
        'ifttt': IFTTTNode,
        'hue': HueNode,

        #'timetracker': TimetrackerNode,
        'or': OrNode,
        'and': AndNode,
        'not': NotNode,
        'delay': DelayNode,
        'inputsmoother': InputSmootherNode,
        'suppressor': SuppressorNode,
        'change': ChangeNode,
        'memory': MemoryNode,
    }

    def __init__(self, username):
        super().__init__(username)

        self.nodes = OrderedDict([])
        self.actions = []
        self.re = []
        self.values = None

        self.update_nodes()

    def update_nodes(self):
        nodes = []

        acts = list(db.actions.find())

        node_ids = [str(r["_id"]) for r in acts]

        for r in acts:
            if "action" in NodeManager.node_types[r["platform"]].output_types:
                # automatically smooth activity -> action connections
                # HUGE assumption: only 1 input endpoint
                # on assumption that activity labels are not in node_ids

                activity_inputs = [[inp for inp in r["data"]["inputs"][0] if inp["id"] not in node_ids]]
                nonactivity_inputs = [[inp for inp in r["data"]["inputs"][0] if inp["id"] in node_ids]]

                #print("activity: " + str(activity_inputs))
                #print("nonactivity: " + str(nonactivity_inputs))

                if len(activity_inputs) > 0:
                    timerange = TimeRangeNode(uuid.uuid4(), self, r["data"])

                    smoother = InputSmootherNode(uuid.uuid4(), self, r["data"])
                    smoother.inputs = activity_inputs

                    andnode = AndNode(uuid.uuid4(), self, None)
                    andnode.inputs = [[{"index": 0, "id": smoother.id}], [{"index": 0, "id": timerange.id}]]

                    nodes.append(timerange)
                    nodes.append(smoother)
                    nodes.append(andnode)

                ornode = OrNode(uuid.uuid4(), self, None)
                ornode.inputs = nonactivity_inputs
                nodes.append(ornode)

                if len(activity_inputs) > 0:
                    ornode.inputs[0].append({"id": andnode.id, "index": 0})

                act = NodeManager.node_types[r["platform"]](str(r["_id"]), self, r["data"])
                act.inputs = [[{"index":0, "id": ornode.id}]]
                nodes.append(act)
            else:
                act = NodeManager.node_types[r["platform"]](str(r["_id"]), self, r["data"])
                act.inputs = r["data"]["inputs"]
                nodes.append(act)


        nodes = topo_sort(nodes)
        self.nodes = OrderedDict([(n.id, n) for n in nodes])

        #logger.debug("nodes: " + str(self.nodes))

    def combine_actions(self, old_actions, new_actions):
        return old_actions + new_actions

    def on_event(self, event, data):
        for node_id, node in self.nodes.items():
            node.on_event(event, data)

        if event == "activity":
            all_values = {}

            classes = cm.cons[self.username]["activitylearner"].classes

            for c in classes:
                all_values[c] = [False]

            logger.debug("graph inputs: {}".format(data))
            all_values[data] = [True]

            for node_id, node in self.nodes.items():
                all_args = []

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

            #logger.debug("graph outputs: {}".format(all_values))

            #logger.debug("comparing states")
            fired_manually, fired_actions = compare_states(self.nodes, self.values, all_values)
            logger.debug(str(fired_manually))
            logger.debug(str(fired_actions))

            man_all = False

            if len(fired_manually) > 0:
                man_all = True
                logger.debug("GOD HAS DESCENDED")

                #logger.debug("fa: " + str(fired_actions))
                for v in fired_actions:
                    #logger.debug("v: " + str(all_values[v]))
                    for vv in all_values[v]:
                        #logger.debug("vv: " + str(vv))
                        vv["manual"] = True
                        vv["manual_time"] = time.time()

            self.values = all_values
            #logger.debug("node manager values: {}".format(self.values))

            actions = []

            for key, val in all_values.items():
                for element in val:
                    if isinstance(element, dict) and "platform" in element and not element in actions:
                        n = self.nodes[key]

                        if man_all:
                            element["manual"] = True
                            element["manual_time"] = time.time()

                        if "manual" in element:
                            element.pop("confirmation", None)

                        # is checking state here appropriate?
                        if n.check_state:
                            #if ("manual" in element and element["manual"])\
                            if not cm.states[self.username].satisfied(element['platform'], element['data']):
                                #change = cm.states[self.username].should_change(element)
                                #logger.debug("change: {}".format(change))

                                #if change:
                                actions.append(element)
                        else:
                            actions.append(element)

            self.actions = self.combine_actions(self.actions, actions)
            logger.debug(str(self.actions))

    def execute(self):
        actions = self.actions
        self.actions = []
        return actions
