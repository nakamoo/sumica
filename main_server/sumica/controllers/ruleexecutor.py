from flask import current_app
import coloredlogs
import logging
import json

from controllers.controller import Controller

from utils import db

logger = logging.getLogger(__name__)
coloredlogs.install(level=current_app.config['LOG_LEVEL'], logger=logger)


class RuleExecutor(Controller):
    def __init__(self, username):
        super().__init__(username)

        # read database, create rules
        self.action = None

    def on_event(self, event, data):
        if event == "activity":
            logger.debug(data)
            # get action command based on rules
            if data == "phone":
                hue_state = json.dumps([{'id': '1', 'state': {'bri': 254, 'hue': 33016, 'on': True, 'sat': 53}},
                        {'id': '2', 'state': {'bri': 254, 'hue': 33016, 'on': True, 'sat': 53}},
                        {'id': '3', 'state': {'bri': 254, 'hue': 33016, 'on': True, 'sat': 53}}])
                self.action = {'platform': 'hue', 'data': hue_state}
            else:
                hue_state = json.dumps([{'id': '1', 'state': {'on': False}},
                                        {'id': '2', 'state': {'on': False}},
                                        {'id': '3', 'state': {'on': False}}])
                self.action = {'platform': 'hue', 'data': hue_state}

    def execute(self):
        if self.action:
            yield [self.action]

        self.action = None