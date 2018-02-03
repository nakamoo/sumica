import time
import os
import random
import traceback
import importlib
import threading
from _thread import start_new_thread
from collections import OrderedDict
import types

from flask import Flask, current_app

import coloredlogs
import logging

from controllers.features import FeatureExtractor
from controllers.chatbot import Chatbot
from controllers.speechbot import Speechbot
from controllers.activitylearner import ActivityLearner
from controllers.ruleexecutor import RuleExecutor

from controllers.reminder import Reminder
from controllers.alarm import Alarm
from controllers.timetracker import TimeTracker

from statetracker import StateTracker
from server_actors import hue_actor
from utils import log_command


logger = logging.getLogger(__name__)
coloredlogs.install(level=current_app.config['LOG_LEVEL'], logger=logger)


def global_event(event, data):
    Chatbot.on_global_event(event, data)


def standard_controllers(username):
    return OrderedDict([
        ("featureextractor", FeatureExtractor(username)),
        ("chatbot", Chatbot(username)),
        ("speechbot", Speechbot(username)),
        ("activitylearner", ActivityLearner(username)),
        ("ruleexecutor", RuleExecutor(username)),

        ("alarm", Alarm(username)),
        ("timetracker", TimeTracker(username))
    ])


def trigger_controllers(user, event, data):
    if user is None:
        global_event(event, data)
    else:
        for c in cons[user].values():
            c.on_event(event, data)

# to be set by launcher
platforms = None
cons = dict()
states = dict()
# for stateless test commands (probably from browser)
test_commands = dict()
test_commands[current_app.config['USER']] = []

def initialize(platform_mods):
    global cons, platforms

    platforms = {p.platform_name: p for p in platform_mods}

    # TODO: use DB
    for user in [current_app.config['USER']]:
        cons[user] = standard_controllers(user)
        states[user] = StateTracker()

def server_execute(username, command):
    platform = command["platform"]
    data = command["data"]

    # TODO e.g. tts not in platforms
    if platform in platforms:
        send_to_client = platforms[platform].execute(data)
        logger.debug("server execute: {}, {}".format(platform, send_to_client))

        return send_to_client

    return True

def client_execute(username):
    commands = []

    for con_name, controller in cons[username].items():
        con_commands = controller.execute()

        if isinstance(con_commands, types.GeneratorType):
            con_commands = next(con_commands)

        #logger.debug("{}: {}".format(con_name, con_commands))

        for command in con_commands:
            commands.append(command)

            if command:
                log_command(command, controller)

    # prioritize test actions over controllers
    for test in test_commands[username]:
        p = test['platform']

        # remove conflicting actions
        commands = [c for c in commands if p != test['platform']]

        commands.append(test)

    test_commands[username].clear()

    if len(commands) > 0:
        logger.debug("commands: {}".format(commands))

    states[username].track(commands)

    # ???
    commands = [[c] for c in commands]

    return commands