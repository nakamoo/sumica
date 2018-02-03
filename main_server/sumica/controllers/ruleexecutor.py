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

        self.history = []

        self.update_rules()

    def update_rules(self):
        self.rules = []

        rec = list(db.actions.find())

        def tosecs(act):
            tokens = act.split()
            if act == "immediate":
                return 0
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
            now = datetime.datetime.now()
            now_min = now.hour * 60 + now.minute

            self.history.append([time.time(), data])

            def hit(activity, activation):
                if len(self.history) <= 0:
                    return False

                hits = 0
                tot = 0

                if activation == 0:
                    t, act = self.history[-1]

                    if act == activity:
                        return True
                else:
                    for t, act in self.history[::-1]:
                        if time.time() - t > activation:
                            break

                        if act == activity:
                            hits += 1
                        tot += 1

                    if tot <= 0:
                        return False

                    logger.debug('{} {}'.format(hits, tot))

                    return float(hits / tot) > 0.5

            actions = []

            # get action command based on rules
            for rule in self.rules:
                if hit(rule['activity'], rule['activation']) and (
                        rule['timerange'][0] == rule['timerange'][1] or (
                        rule['timerange'][0] <= now_min < rule['timerange'][1])):
                    action = rule['action']
                    if ('continuous' in action and action['continuous']) or not cm.states[self.username].satisfied(
                            action['platform'], action['data']):
                        send_to_client = cm.server_execute(self.username, action)

                        if send_to_client:
                            actions.append(rule['action'])

            self.actions = actions

    def execute(self):
        yield self.actions
        self.actions = []
