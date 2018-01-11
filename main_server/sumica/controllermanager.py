import time
import os
import traceback
import importlib
import threading
from _thread import start_new_thread

from flask import Flask, current_app

import coloredlogs
import logging

from controllers.features import FeatureExtractor
from controllers.chatbot import Chatbot
from controllers.speechbot import Speechbot


logger = logging.getLogger(__name__)
coloredlogs.install(level=current_app.config['LOG_LEVEL'], logger=logger)


def global_event(event, data):
    FeatureExtractor.on_global_event(event, data)
    Chatbot.on_global_event(event, data)
    Speechbot.on_global_event(event, data)
    Snapshot.on_global_event(event, data)
    Settings.on_global_event(event, data)


def standard_controllers(user_name):
    return [FeatureExtractor(user_name), Chatbot(user_name), Speechbot(user_name)]


def trigger_controllers(user, event, data):
    if user is None:
        global_event(event, data)
    else:
        for c in cons[user]:
            c.on_event(event, data)


# TODO: use DB
cons = dict()
cons[current_app.config['USER']] = standard_controllers(current_app.config['USER'])
