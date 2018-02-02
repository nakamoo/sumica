from flask import current_app
import coloredlogs
import logging
import json
import time
import datetime

from controllers.controller import Controller

from utils import db
import controllermanager as cm

logger = logging.getLogger(__name__)
coloredlogs.install(level=current_app.config['LOG_LEVEL'], logger=logger)


def data2command(data):
    platform = data["platform"]
    command = cm.platforms[platform].data2command(data["data"])
    return command


class RuleExecutor(Controller):
    def __init__(self, username):
        super().__init__(username)

        # read database, create rules
        self.actions = []

        self.rules = []

        self.last_change = None
        self.last_activity = None

        self.update_rules()

    def update_rules(self):
        self.rules = []

        rec = list(db.actions.find())

        def tosecs(act):
            tokens = act.split()
            if "minute" in tokens[1]:
                return int(tokens[0]) * 60
            elif "second" in tokens[1]:
                return int(tokens[0])
            else:
                return 0

        for r in rec:
            act = data2command(r)

            for inp in r["data"]["inputs"]:
                rule = {'activity': inp, 'timerange': [r["data"]["startTime"], r["data"]["endTime"]],
                        'activation': tosecs(r["data"]["activation"]), 'action': act}
                self.rules.append(rule)

        logger.debug("rules: " + str(self.rules))

    def on_event(self, event, data):
        if event == "activity":
            if self.last_activity != data:
                self.last_activity = data
                self.last_change = time.time()

            activation = time.time() - self.last_change
            now = datetime.datetime.now()
            now_min = now.hour * 60 + now.minute

            logger.debug("activity: {}, activation: {}".format(data, activation))

            # get action command based on rules
            for rule in self.rules:
                if data == rule['activity'] and activation > rule['activation'] and (
                        rule['timerange'][0] == rule['timerange'][1] or (
                        rule['timerange'][0] <= now_min < rule['timerange'][1])):
                    self.actions.append(rule['action'])

    def execute(self):
        yield self.actions
        self.actions = []
